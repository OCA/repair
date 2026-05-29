# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models
from odoo.tools import float_is_zero


class RepairOrder(models.Model):
    _inherit = "repair.order"

    consumption_picking_id = fields.Many2one(
        "stock.picking", string="Consumption Picking", readonly=True, copy=False
    )
    repair_consumption_step = fields.Boolean(
        related="warehouse_id.repair_consumption_step"
    )
    state = fields.Selection(
        # Put "consumption" step before "done" step (for UI)
        selection_add=[("consumption", "Waiting Consumption"), ("done",)],
        ondelete={"consumption": "set done"},
    )

    def action_view_consumption_picking(self):
        self.ensure_one()
        return {
            "name": "Repair Consumption Picking",
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "view_mode": "form",
            "res_id": self.consumption_picking_id.id,
        }

    def action_repair_done(self):
        need_consumption_step = self.filtered("repair_consumption_step")
        res = super(RepairOrder, self - need_consumption_step).action_repair_done()
        for rec in need_consumption_step:
            rec_res = super(
                RepairOrder, rec.with_context(dont_validate_repair_move=True)
            ).action_repair_done()
            res.update(rec_res)
            moves = self.env["stock.move"].search(
                [("repair_id", "=", rec.id), ("state", "!=", "cancel")]
            )
            if not moves:
                continue
            picking = self.env["stock.picking"].create(
                {
                    "picking_type_id": rec.warehouse_id.repair_consumption_picking_type_id.id,
                    "origin": rec.name,
                    "move_ids": [Command.set(moves.ids)],
                }
            )

            # Preserve lot info before unlink the move lines
            move_id_lots_ids_map = {}
            for move in moves:
                move_id_lots_ids_map[move.id] = move.move_line_ids.mapped("lot_id").ids

            moves.move_line_ids.unlink()
            moves._action_confirm()
            # need exists because confirm() may merge moves
            moves.exists()._action_assign()

            # Reset lot_id on the new move lines
            for move in moves:
                lot_ids = move_id_lots_ids_map.get(move.id)
                if not lot_ids:
                    continue
                for line in move.move_line_ids:
                    if not line.lot_id:
                        line.lot_id = lot_ids.pop(0)

            rec.consumption_picking_id = picking
            rec.state = "consumption"
        return res

    def action_repair_cancel(self):
        res = super().action_repair_cancel()
        if self.consumption_picking_id and self.consumption_picking_id.state not in (
            "done",
            "cancel",
        ):
            self.consumption_picking_id.action_cancel()
        return res

    def action_repair_end(self):
        super().action_repair_end()
        need_consumption_step = self.filtered("consumption_picking_id")
        need_consumption_step.state = "consumption"
        return True

    def _action_consumption_done(self):
        for rec in self:
            state = "done"
            if not rec.invoice_id and rec.invoice_method == "after_repair":
                state = "2binvoiced"
            rec.state = state

    def _update_parts(self, return_consumption_moves):
        """Update Repair Order operations based on unconsumed quantities.

        This method reduces the demand (product_uom_qty) on the repair order
        lines by matching them against moves that were cancelled/returned
        during the partial consumption process. It uses a 'pop' logic across
        multiple lines of the same product until the returned quantity
        is fully accounted for.

        Complexity Note:
        The pop logic here is needed because there might be more than one repair.line
        per product.
        """
        self.ensure_one()
        operations_to_delete = self.env["repair.line"]
        for return_move in return_consumption_moves:
            remaining_qty = return_move.product_uom_qty
            operations = self.operations.filtered(
                lambda o: o.product_id == return_move.product_id
            )
            while (
                not float_is_zero(
                    remaining_qty, precision_rounding=return_move.product_uom.rounding
                )
                and operations
            ):
                # TODO: find a better solution to extract the "best matching" operation
                # instead of simply taking the first
                operation = operations[0]
                qty_before_update = operation.product_uom_qty
                operation.product_uom_qty -= min(
                    operation.product_uom_qty, remaining_qty
                )
                if float_is_zero(
                    operation.product_uom_qty,
                    precision_rounding=operation.product_uom.rounding,
                ):
                    operations_to_delete |= operation

                remaining_qty -= qty_before_update - operation.product_uom_qty
                operations -= operation

        if operations_to_delete:
            operations_to_delete.unlink()
