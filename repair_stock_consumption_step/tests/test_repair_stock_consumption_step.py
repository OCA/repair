# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairStockConsumptionStep(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Product to repair", "type": "product"}
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "product to consume", "type": "product"}
        )
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "WH", "code": "wh_test"}
        )
        cls.repair_loc = cls.warehouse.lot_stock_id
        cls.production_location = cls.env["stock.location"].search(
            [("usage", "=", "production")], limit=1
        )
        cls.consumption_type = cls.env["stock.picking.type"].create(
            {
                "name": "Consumption",
                "code": "internal",
                "warehouse_id": cls.warehouse.id,
                "sequence_code": "PREP",
                "default_location_src_id": cls.repair_loc.id,
                "default_location_dest_id": cls.production_location.id,
            }
        )
        cls.repair = cls.env["repair.order"].create(
            {
                "partner_id": cls.partner.id,
                "product_id": cls.product.id,
                "location_id": cls.repair_loc.id,
            }
        )
        cls.line = cls.env["repair.line"].create(
            {
                "name": "replace product",
                "repair_id": cls.repair.id,
                "type": "add",
                "price_unit": 100,
                "product_id": cls.product_c.id,
                "product_uom_qty": 2.0,
                "location_id": cls.repair_loc.id,
                "lot_id": cls.env["stock.lot"]
                .create({"name": "Test Lot", "product_id": cls.product_c.id})
                .id,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.repair_loc, 1.0
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_c, cls.repair_loc, 10.0
        )
        cls.repair.action_validate()
        cls.repair.action_repair_ready()
        cls.repair.action_repair_start()

    @classmethod
    def _do_picking(cls, picking):
        for move in picking.move_ids:
            move.quantity_done = move.product_qty
        picking._action_done()

    def test_repair_done_no_consumption_step(self):
        self.repair.action_repair_end()
        moves = self.env["stock.move"].search([("repair_id", "=", self.repair.id)])
        self.assertTrue(moves)
        self.assertTrue(all(m.state == "done" for m in moves))
        self.assertFalse(self.repair.consumption_picking_id)

    def test_repair_done_with_consumption_step(self):
        self.warehouse.repair_consumption_step = True
        self.warehouse.repair_consumption_picking_type_id = self.consumption_type
        self.repair.action_repair_end()
        self.assertEqual(self.repair.state, "consumption")
        self.assertTrue(self.repair.consumption_picking_id)
        moves = self.env["stock.move"].search([("repair_id", "=", self.repair.id)])
        pick = self.repair.consumption_picking_id
        self.assertEqual(self.repair.operations.lot_id, pick.move_line_ids.lot_id)
        self.assertTrue(moves)
        self.assertEqual(pick.move_ids, moves)
        self.assertEqual(
            pick.location_id,
            self.warehouse.repair_consumption_picking_type_id.default_location_src_id,
        )
        self.assertEqual(
            pick.location_dest_id,
            self.warehouse.repair_consumption_picking_type_id.default_location_dest_id,
        )
        self.assertSetEqual(set(moves.mapped("state")), {"assigned"})
        self.assertIn(pick.state, "assigned")
        self.assertEqual(pick.move_line_ids, moves.move_line_ids)
        self._do_picking(pick)
        self.assertEqual(self.repair.state, "done")

    def test_repair_done_with_consumption_step_invoice_after_repair(self):
        self.warehouse.repair_consumption_step = True
        self.warehouse.repair_consumption_picking_type_id = self.consumption_type
        self.repair.invoice_method = "after_repair"
        self.repair.action_repair_end()
        self.assertEqual(self.repair.state, "consumption")
        self._do_picking(self.repair.consumption_picking_id)
        self.assertEqual(self.repair.state, "2binvoiced")
