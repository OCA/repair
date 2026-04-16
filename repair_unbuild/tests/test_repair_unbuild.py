# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairUnbuild(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Locations
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.repair_type = cls.env["stock.picking.type"].search(
            [
                ("code", "=", "repair_operation"),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )
        # Products
        cls.product_final = cls.env["product.product"].create(
            {
                "name": "Final Product",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.product_tube = cls.env["product.product"].create(
            {
                "name": "Tube",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.product_rubber = cls.env["product.product"].create(
            {
                "name": "Rubber Part",
                "type": "product",
            }
        )
        # BoM: Final Product = 1 Tube + 2 Rubber Parts
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_final.product_tmpl_id.id,
                "product_qty": 1,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_tube.id,
                            "product_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_rubber.id,
                            "product_qty": 2,
                        },
                    ),
                ],
            }
        )

    def _create_lot(self, product, name):
        return self.env["stock.lot"].create(
            {
                "name": name,
                "product_id": product.id,
                "company_id": self.env.company.id,
            }
        )

    def _produce_mo(self, lot_final, lot_tube):
        """Create and complete a manufacturing order."""
        Quant = self.env["stock.quant"]
        Quant._update_available_quantity(
            self.product_tube,
            self.stock_location,
            1,
            lot_id=lot_tube,
        )
        Quant._update_available_quantity(
            self.product_rubber,
            self.stock_location,
            2,
        )
        mo = self.env["mrp.production"].create(
            {
                "product_id": self.product_final.id,
                "product_qty": 1,
                "bom_id": self.bom.id,
            }
        )
        mo.action_confirm()
        mo.action_assign()
        mo_form = Form(mo)
        mo_form.qty_producing = 1
        mo_form.lot_producing_id = lot_final
        mo = mo_form.save()
        mo.move_raw_ids.picked = True
        res = mo.button_mark_done()
        if res is not True:
            ctx = dict(res.get("context", {}))
            wizard = self.env[res["res_model"]].with_context(**ctx).create({})
            wizard.action_confirm()
        self.assertEqual(mo.state, "done")
        return mo

    def _do_repair(self, lot, move_vals_list, move_lots=None):
        """Create and complete a repair order.

        Args:
            lot: serial lot of the product being repaired.
            move_vals_list: list of dicts for the repair move lines.
            move_lots: optional dict {(product_id, repair_line_type): lot}
                to assign specific lots to tracked repair move lines.
        """
        repair = self.env["repair.order"].create(
            {
                "picking_type_id": self.repair_type.id,
                "product_id": self.product_final.id,
                "lot_id": lot.id,
                "product_uom": self.product_final.uom_id.id,
                "location_id": self.stock_location.id,
                "move_ids": [(0, 0, vals) for vals in move_vals_list],
            }
        )
        repair.action_validate()
        repair.action_repair_start()
        for move in repair.move_ids:
            move.quantity = move.product_uom_qty
            if move_lots:
                key = (move.product_id.id, move.repair_line_type)
                lot_id = move_lots.get(key)
                if lot_id:
                    move.move_line_ids.lot_id = lot_id
            move.picked = True
        repair.action_repair_end()
        self.assertEqual(repair.state, "done")
        return repair

    def _do_unbuild(self, mo, lot):
        """Create and execute an unbuild order."""
        unbuild = self.env["mrp.unbuild"].create(
            {
                "product_id": self.product_final.id,
                "bom_id": self.bom.id,
                "mo_id": mo.id,
                "lot_id": lot.id,
                "product_qty": 1,
                "location_id": self.stock_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        unbuild.action_unbuild()
        self.assertEqual(unbuild.state, "done")
        return unbuild

    def test_unbuild_no_repair(self):
        """Standard unbuild without repairs behaves normally."""
        lot_final = self._create_lot(self.product_final, "SN-F01")
        lot_tube = self._create_lot(self.product_tube, "SN-T01")
        mo = self._produce_mo(lot_final, lot_tube)
        unbuild = self._do_unbuild(mo, lot_final)
        tube_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == self.product_tube
        )
        rubber_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == self.product_rubber
        )
        self.assertEqual(tube_move.move_line_ids.lot_id, lot_tube)
        self.assertEqual(rubber_move.product_uom_qty, 2)

    def test_unbuild_serial_swap(self):
        """Scenario 1: Tube serial swapped during repair."""
        lot_final = self._create_lot(self.product_final, "SN-F02")
        lot_tube_old = self._create_lot(self.product_tube, "SN-T-OLD")
        lot_tube_new = self._create_lot(self.product_tube, "SN-T-NEW")
        mo = self._produce_mo(lot_final, lot_tube_old)
        self.env["stock.quant"]._update_available_quantity(
            self.product_tube,
            self.stock_location,
            1,
            lot_id=lot_tube_new,
        )
        self._do_repair(
            lot_final,
            [
                {
                    "repair_line_type": "remove",
                    "product_id": self.product_tube.id,
                    "product_uom_qty": 1,
                },
                {
                    "repair_line_type": "add",
                    "product_id": self.product_tube.id,
                    "product_uom_qty": 1,
                },
            ],
            move_lots={
                (self.product_tube.id, "remove"): lot_tube_old,
                (self.product_tube.id, "add"): lot_tube_new,
            },
        )
        unbuild = self._do_unbuild(mo, lot_final)
        tube_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == self.product_tube
        )
        self.assertEqual(tube_move.move_line_ids.lot_id, lot_tube_new)

    def test_unbuild_missing_component(self):
        """Scenario 2: One rubber part removed during repair."""
        lot_final = self._create_lot(self.product_final, "SN-F03")
        lot_tube = self._create_lot(self.product_tube, "SN-T03")
        mo = self._produce_mo(lot_final, lot_tube)
        self._do_repair(
            lot_final,
            [
                {
                    "repair_line_type": "remove",
                    "product_id": self.product_rubber.id,
                    "product_uom_qty": 1,
                },
            ],
        )
        unbuild = self._do_unbuild(mo, lot_final)
        rubber_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == self.product_rubber
        )
        self.assertEqual(rubber_move.product_uom_qty, 1)

    def test_unbuild_component_fully_removed(self):
        """All rubber parts removed: unbuild skips them entirely."""
        lot_final = self._create_lot(self.product_final, "SN-F04")
        lot_tube = self._create_lot(self.product_tube, "SN-T04")
        mo = self._produce_mo(lot_final, lot_tube)
        self._do_repair(
            lot_final,
            [
                {
                    "repair_line_type": "remove",
                    "product_id": self.product_rubber.id,
                    "product_uom_qty": 2,
                },
            ],
        )
        unbuild = self._do_unbuild(mo, lot_final)
        rubber_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == self.product_rubber
        )
        self.assertFalse(rubber_move)

    def test_unbuild_new_component_added(self):
        """Scenario 3: New component added during repair (not in BoM)."""
        lot_final = self._create_lot(self.product_final, "SN-F05")
        lot_tube = self._create_lot(self.product_tube, "SN-T05")
        mo = self._produce_mo(lot_final, lot_tube)
        product_gasket = self.env["product.product"].create(
            {
                "name": "Gasket",
                "type": "product",
            }
        )
        self.env["stock.quant"]._update_available_quantity(
            product_gasket,
            self.stock_location,
            1,
        )
        self._do_repair(
            lot_final,
            [
                {
                    "repair_line_type": "add",
                    "product_id": product_gasket.id,
                    "product_uom_qty": 1,
                },
            ],
        )
        unbuild = self._do_unbuild(mo, lot_final)
        gasket_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == product_gasket
        )
        self.assertEqual(len(gasket_move), 1)
        self.assertEqual(gasket_move.product_uom_qty, 1)

    def test_unbuild_multiple_repairs_serial_chain(self):
        """Multiple repairs: T1 swapped to T2, then T2 to T3."""
        lot_final = self._create_lot(self.product_final, "SN-F06")
        lot_t1 = self._create_lot(self.product_tube, "SN-T-V1")
        lot_t2 = self._create_lot(self.product_tube, "SN-T-V2")
        lot_t3 = self._create_lot(self.product_tube, "SN-T-V3")
        mo = self._produce_mo(lot_final, lot_t1)
        swap_vals = [
            {
                "repair_line_type": "remove",
                "product_id": self.product_tube.id,
                "product_uom_qty": 1,
            },
            {
                "repair_line_type": "add",
                "product_id": self.product_tube.id,
                "product_uom_qty": 1,
            },
        ]
        self.env["stock.quant"]._update_available_quantity(
            self.product_tube,
            self.stock_location,
            1,
            lot_id=lot_t2,
        )
        self._do_repair(
            lot_final,
            swap_vals,
            move_lots={
                (self.product_tube.id, "remove"): lot_t1,
                (self.product_tube.id, "add"): lot_t2,
            },
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product_tube,
            self.stock_location,
            1,
            lot_id=lot_t3,
        )
        self._do_repair(
            lot_final,
            swap_vals,
            move_lots={
                (self.product_tube.id, "remove"): lot_t2,
                (self.product_tube.id, "add"): lot_t3,
            },
        )
        unbuild = self._do_unbuild(mo, lot_final)
        tube_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == self.product_tube
        )
        self.assertEqual(tube_move.move_line_ids.lot_id, lot_t3)

    def test_unbuild_lot_tracked_product_unaffected(self):
        """Lot-tracked (non-serial) products are NOT affected by the module."""
        product_widget = self.env["product.product"].create(
            {
                "name": "Widget (lot)",
                "type": "product",
                "tracking": "lot",
            }
        )
        product_screw = self.env["product.product"].create(
            {
                "name": "Screw",
                "type": "product",
            }
        )
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": product_widget.product_tmpl_id.id,
                "product_qty": 1,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product_screw.id,
                            "product_qty": 5,
                        },
                    ),
                ],
            }
        )
        lot_widget = self._create_lot(product_widget, "WGT-LOT")
        Quant = self.env["stock.quant"]
        Quant._update_available_quantity(
            product_screw,
            self.stock_location,
            5,
        )
        mo = self.env["mrp.production"].create(
            {
                "product_id": product_widget.id,
                "product_qty": 1,
                "bom_id": bom.id,
            }
        )
        mo.action_confirm()
        mo.action_assign()
        mo_form = Form(mo)
        mo_form.qty_producing = 1
        mo_form.lot_producing_id = lot_widget
        mo = mo_form.save()
        mo.move_raw_ids.picked = True
        res = mo.button_mark_done()
        if res is not True:
            ctx = dict(res.get("context", {}))
            self.env[res["res_model"]].with_context(**ctx).create({}).action_confirm()
        self.assertEqual(mo.state, "done")
        repair = self.env["repair.order"].create(
            {
                "picking_type_id": self.repair_type.id,
                "product_id": product_widget.id,
                "lot_id": lot_widget.id,
                "product_uom": product_widget.uom_id.id,
                "location_id": self.stock_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "repair_line_type": "remove",
                            "product_id": product_screw.id,
                            "product_uom_qty": 2,
                        },
                    ),
                ],
            }
        )
        repair.action_validate()
        repair.action_repair_start()
        for move in repair.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        repair.action_repair_end()
        self.assertEqual(repair.state, "done")
        unbuild = self.env["mrp.unbuild"].create(
            {
                "product_id": product_widget.id,
                "bom_id": bom.id,
                "mo_id": mo.id,
                "lot_id": lot_widget.id,
                "product_qty": 1,
                "location_id": self.stock_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        unbuild.action_unbuild()
        self.assertEqual(unbuild.state, "done")
        screw_move = unbuild.produce_line_ids.filtered(
            lambda m: m.product_id == product_screw
        )
        self.assertEqual(
            screw_move.product_uom_qty,
            5,
            "Lot-tracked product should NOT be adjusted by repair history",
        )
