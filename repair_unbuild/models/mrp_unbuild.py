# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import models
from odoo.tools import float_compare, float_round


class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    def _get_repair_orders(self):
        """Find completed repair orders for the unbuild's product lot.

        Only applies to serial-tracked products where each lot uniquely
        identifies a single unit, making the repair history unambiguous.
        """
        self.ensure_one()
        if not self.lot_id or not self.mo_id or self.product_id.tracking != "serial":
            return self.env["repair.order"]
        return self.env["repair.order"].search(
            [
                ("lot_id", "=", self.lot_id.id),
                ("product_id", "=", self.product_id.id),
                ("state", "=", "done"),
            ],
            order="create_date asc",
        )

    def _get_net_removed_components(self, repairs):
        """Compute net removed quantities per product from repair history.

        A component is considered net-removed if the total quantity removed
        (via 'remove' or 'recycle' operations) exceeds the total quantity
        added back for the same product.

        Returns dict: {product recordset: net_removed_qty}
        """
        repair_moves = repairs.move_ids.filtered(
            lambda m: m.state == "done" and m.repair_line_type
        )
        removed = defaultdict(float)
        added = defaultdict(float)
        for move in repair_moves:
            if move.repair_line_type in ("remove", "recycle"):
                removed[move.product_id] += move.product_uom_qty
            elif move.repair_line_type == "add":
                added[move.product_id] += move.product_uom_qty
        net_removed = {}
        for product, qty in removed.items():
            net = qty - added.get(product, 0.0)
            if float_compare(net, 0, precision_rounding=product.uom_id.rounding) > 0:
                net_removed[product] = net
        return net_removed

    def _get_new_repair_components(self, repairs):
        """Find components added during repair that weren't in the original MO.

        Returns dict: {product recordset: {qty, uom, lots: [(qty, lot)]}}
        """
        mo_product_ids = set(
            self.mo_id.move_raw_ids.filtered(lambda m: m.state == "done").mapped(
                "product_id.id"
            )
        )
        repair_add_moves = repairs.move_ids.filtered(
            lambda m: m.state == "done"
            and m.repair_line_type == "add"
            and m.product_id.id not in mo_product_ids
        )
        new_components = {}
        for move in repair_add_moves:
            if move.product_id not in new_components:
                new_components[move.product_id] = {
                    "qty": 0.0,
                    "uom": move.product_uom,
                    "lots": [],
                }
            new_components[move.product_id]["qty"] += move.product_uom_qty
            for ml in move.move_line_ids.filtered(lambda line: line.quantity > 0):
                if ml.lot_id:
                    new_components[move.product_id]["lots"].append(
                        (ml.quantity, ml.lot_id)
                    )
        return new_components

    def _get_repair_lot_swaps(self, product):
        """Build a chronological list of lot swaps for a given component.

        For each completed repair on the unbuild's lot, pair its
        ``remove``/``recycle`` move lines with its ``add`` move lines
        for ``product``. Each pair represents a quantity swap from the
        removed lot to the added lot.

        Returns a list of ``(from_lot, to_lot, qty)`` tuples in
        chronological order.
        """
        self.ensure_one()
        repairs = self._get_repair_orders()
        swaps = []
        if not repairs:
            return swaps
        for repair in repairs:
            product_moves = repair.move_ids.filtered(
                lambda m, p=product: m.state == "done" and m.product_id == p
            )
            removes = []
            adds = []
            for move in product_moves:
                bucket = None
                if move.repair_line_type in ("remove", "recycle"):
                    bucket = removes
                elif move.repair_line_type == "add":
                    bucket = adds
                if bucket is None:
                    continue
                for ml in move.move_line_ids.filtered(
                    lambda line: line.quantity > 0 and line.lot_id
                ):
                    bucket.append([ml.lot_id, ml.quantity])
            ri = ai = 0
            while ri < len(removes) and ai < len(adds):
                from_lot, from_qty = removes[ri]
                to_lot, to_qty = adds[ai]
                paired = min(from_qty, to_qty)
                if paired > 0:
                    swaps.append((from_lot, to_lot, paired))
                removes[ri][1] -= paired
                adds[ai][1] -= paired
                if removes[ri][1] <= 0:
                    ri += 1
                if adds[ai][1] <= 0:
                    ai += 1
        return swaps

    def _get_lot_substitutions(self, product, original_lot, taken_qty):
        """Compute final lot distribution for ``taken_qty`` units of
        ``original_lot`` after applying repair history.

        Handles partial lot swaps: if a batch of 5 units of L1 only had
        1 unit swapped to L2, returns ``[(L1, 4), (L2, 1)]`` rather than
        wholesale-swapping the entire batch.

        Returns a list of ``(lot, qty)`` tuples summing to ``taken_qty``.
        """
        self.ensure_one()
        if not original_lot:
            return [(original_lot, taken_qty)]
        swaps = self._get_repair_lot_swaps(product)
        if not swaps:
            return [(original_lot, taken_qty)]
        state = {original_lot: taken_qty}
        for from_lot, to_lot, swap_qty in swaps:
            available = state.get(from_lot, 0)
            applicable = min(swap_qty, available)
            if applicable <= 0:
                continue
            state[from_lot] = available - applicable
            state[to_lot] = state.get(to_lot, 0) + applicable
            if state[from_lot] <= 0:
                del state[from_lot]
        return [(lot, qty) for lot, qty in state.items() if qty > 0]

    def _generate_produce_moves(self):
        moves = super()._generate_produce_moves()
        for unbuild in self:
            if not unbuild.mo_id or not unbuild.lot_id:
                continue
            repairs = unbuild._get_repair_orders()
            if not repairs:
                continue
            net_removed = unbuild._get_net_removed_components(repairs)
            if not net_removed:
                continue
            unbuild_moves = moves.filtered(lambda m: m.unbuild_id == unbuild)  # noqa: B023
            for product, removed_qty in net_removed.items():
                matching = unbuild_moves.filtered(
                    lambda m, p=product: m.product_id == p
                )
                remaining = removed_qty
                for move in matching:
                    if (
                        float_compare(
                            remaining,
                            0,
                            precision_rounding=product.uom_id.rounding,
                        )
                        <= 0
                    ):
                        break
                    qty_to_reduce = min(remaining, move.product_uom_qty)
                    new_qty = move.product_uom_qty - qty_to_reduce
                    if (
                        float_compare(
                            new_qty,
                            0,
                            precision_rounding=move.product_uom.rounding,
                        )
                        <= 0
                    ):
                        moves -= move
                        move.unlink()
                    else:
                        move.product_uom_qty = new_qty
                    remaining -= qty_to_reduce
        return moves

    def _prepare_move_line_vals(self, move, origin_move_line, taken_quantity):
        vals = super()._prepare_move_line_vals(move, origin_move_line, taken_quantity)
        if not (self.lot_id and origin_move_line.lot_id):
            return vals
        if move.product_id.tracking != "serial":
            return vals
        substitutions = self._get_lot_substitutions(
            move.product_id, origin_move_line.lot_id, taken_quantity
        )
        if substitutions and substitutions[0][0] != origin_move_line.lot_id:
            vals["lot_id"] = substitutions[0][0].id
        return vals

    def action_unbuild(self):
        res = super().action_unbuild()
        self._create_repair_added_component_moves()
        return res

    def _create_repair_added_component_moves(self):
        """Create produce moves for components added during repair
        that were not part of the original manufacturing order."""
        self.ensure_one()
        if not self.mo_id or not self.lot_id:
            return
        repairs = self._get_repair_orders()
        if not repairs:
            return
        new_components = self._get_new_repair_components(repairs)
        if not new_components:
            return
        for product, data in new_components.items():
            product_prod_location = product.with_company(
                self.company_id
            ).property_stock_production
            move = self.env["stock.move"].create(
                {
                    "name": self.name,
                    "date": self.create_date,
                    "product_id": product.id,
                    "product_uom_qty": data["qty"],
                    "product_uom": data["uom"].id,
                    "procure_method": "make_to_stock",
                    "location_id": product_prod_location.id,
                    "location_dest_id": self.location_dest_id.id,
                    "warehouse_id": self.location_dest_id.warehouse_id.id,
                    "unbuild_id": self.id,
                    "company_id": self.company_id.id,
                }
            )
            move._action_confirm()
            if data["lots"]:
                for qty, lot in data["lots"]:
                    self.env["stock.move.line"].create(
                        {
                            "move_id": move.id,
                            "product_id": product.id,
                            "product_uom_id": data["uom"].id,
                            "quantity": qty,
                            "lot_id": lot.id,
                            "location_id": move.location_id.id,
                            "location_dest_id": move.location_dest_id.id,
                        }
                    )
            else:
                move.quantity = float_round(
                    data["qty"],
                    precision_rounding=move.product_uom.rounding,
                )
            move.picked = True
            move._action_done()
