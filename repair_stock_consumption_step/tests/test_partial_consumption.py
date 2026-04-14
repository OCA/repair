# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError

from .common import Common


class TestPartialConsumption(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse.repair_consumption_picking_type_id.return_picking_type_id = (
            cls.warehouse.int_type_id
        )

    def _do_repair(self):
        self.repair.action_validate()
        self.repair.action_repair_ready()
        self.repair.action_repair_start()
        self.repair.action_repair_end()

    def _do_partial_consumption(self):
        cons_pick = self.repair.consumption_picking_id
        for move in cons_pick.move_ids.filtered(lambda m: m.product_id == self.product):
            move.quantity_done = move.product_qty
        for move in cons_pick.move_ids.filtered(
            lambda m: m.product_id == self.product_c
        ):
            move.quantity_done = move.product_qty - 1

        res = cons_pick.button_validate()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})
        return wizard

    def _test_partial_consumption_chatter_message(self, return_picking):
        odoobot = self.env.ref("base.partner_root")
        last_message = self.repair.message_ids[0]
        self.assertEqual(last_message.author_id, odoobot)
        self.assertIn(return_picking.name, str(last_message.body))

    def test_partial_consumption_simple(self):
        self._do_repair()
        operation_values_before = self.repair.operations.read(
            [
                "product_id",
                "type",
                "price_unit",
                "location_id",
                "location_dest_id",
                "move_id",
                "lot_id",
            ],
            load=None,  # do not load the name of xToMany fields
        )[0]
        wizard = self._do_partial_consumption()
        res = wizard.action_store_back_spare_parts()
        return_picking = self.env[res["res_model"]].browse(res["res_id"])

        self.assertTrue(return_picking)
        self.assertEqual(return_picking.move_ids.product_id, self.product_c)
        self.assertEqual(return_picking.move_ids.product_uom_qty, 1)
        self.assertRecordValues(
            self.repair.operations, [operation_values_before | {"product_uom_qty": 1}]
        )
        self._test_partial_consumption_chatter_message(return_picking)

    def test_no_spare_parts_consumed(self):
        self._do_repair()

        # Do not consume any spare parts
        cons_pick = self.repair.consumption_picking_id
        for move in cons_pick.move_ids.filtered(lambda m: m.product_id == self.product):
            move.quantity_done = move.product_qty
        res = cons_pick.button_validate()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})

        res = wizard.action_store_back_spare_parts()
        return_picking = self.env[res["res_model"]].browse(res["res_id"])

        self.assertTrue(return_picking)
        self.assertEqual(return_picking.move_ids.product_id, self.product_c)
        self.assertEqual(return_picking.move_ids.product_uom_qty, 2)
        self.assertEqual(len(self.repair.operations), 0)

    def test_partial_consumption_multiple_repair_line_per_product(self):
        self.repair.operations.unlink()
        self.repair.operations = [
            Command.create(
                {
                    "name": "replace product",
                    "type": "add",
                    "price_unit": 100,
                    "product_id": self.product_c.id,
                    "product_uom_qty": qty,
                    "location_id": self.repair_loc.id,
                    "lot_id": self.env["stock.lot"]
                    .create({"name": f"lot test {i}", "product_id": self.product_c.id})
                    .id,
                }
            )
            for i, qty in enumerate((2.0, 5.0))
        ]
        self._do_repair()
        operation_values_before = self.repair.operations.read(
            [
                "product_id",
                "type",
                "price_unit",
                "location_id",
                "location_dest_id",
                "move_id",
                "lot_id",
            ],
            load=None,  # do not load the name of xToMany fields
        )
        wizard = self._do_partial_consumption()
        res = wizard.action_store_back_spare_parts()
        return_picking = self.env[res["res_model"]].browse(res["res_id"])

        self.assertTrue(return_picking)
        self.assertEqual(return_picking.move_ids.product_id, self.product_c)
        self.assertEqual(return_picking.move_ids.product_uom_qty, 1)
        self.assertRecordValues(
            self.repair.operations,
            [
                x | {"product_uom_qty": qty}
                for x, qty in zip(operation_values_before, (1.0, 5.0))
            ],
        )

    def test_partial_consumption_multiple_repair_line_per_product_2(self):
        self.repair.operations.unlink()
        self.repair.operations = [
            Command.create(
                {
                    "name": "replace product",
                    "type": "add",
                    "price_unit": 100,
                    "product_id": self.product_c.id,
                    "product_uom_qty": qty,
                    "location_id": self.repair_loc.id,
                    "lot_id": self.env["stock.lot"]
                    .create({"name": f"lot test {i}", "product_id": self.product_c.id})
                    .id,
                }
            )
            for i, qty in enumerate((2.0, 5.0))
        ]
        self._do_repair()
        operation_values_before = self.repair.operations.read(
            [
                "product_id",
                "type",
                "price_unit",
                "location_id",
                "location_dest_id",
                "move_id",
                "lot_id",
            ],
            load=None,  # do not load the name of xToMany fields
        )

        # Validate very few consumption (to force a 0 qty operation on RO)
        cons_pick = self.repair.consumption_picking_id
        for move in cons_pick.move_ids:
            move.quantity_done = 1
        res = cons_pick.button_validate()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})

        res = wizard.action_store_back_spare_parts()
        return_picking = self.env[res["res_model"]].browse(res["res_id"])

        self.assertTrue(return_picking)
        self.assertEqual(return_picking.move_ids.product_id, self.product_c)
        self.assertEqual(return_picking.move_ids.product_uom_qty, 6)
        self.assertEqual(len(self.repair.operations), 1)
        # Only the second opearation remains as we needed to remove 6 units
        # and we had 2 (for op 1) and 5 (for op 2) before
        self.assertRecordValues(
            self.repair.operations,
            [operation_values_before[1] | {"product_uom_qty": 1}],
        )

    def test_consumption_return_type_necessary(self):
        self._do_repair()
        self.warehouse.repair_consumption_picking_type_id.return_picking_type_id = False
        wizard = self._do_partial_consumption()

        with self.assertRaises(ValidationError):
            wizard.action_store_back_spare_parts()

    def test_can_not_partially_process_repaired_product(self):
        """
        Ensure users can not partially process the repaired products.
        Only spare parts can be partially processed.
        """
        self._do_repair()
        # Process all consumptions moves fully except for the repaired product one
        cons_pick = self.repair.consumption_picking_id
        for move in cons_pick.move_ids:
            move.quantity_done = move.product_qty
        repair = cons_pick.consumption_repair_order_id
        repaired_product_move = cons_pick.move_ids.filtered(
            lambda m: m.product_id == repair.product_id
        )
        repaired_product_move.quantity_done -= 1

        with self.assertRaises(ValidationError):
            cons_pick.button_validate()
