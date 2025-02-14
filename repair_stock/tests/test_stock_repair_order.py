# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestStockRepairOrder(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repair_model = cls.env["repair.order"]
        cls.product_model = cls.env["product.product"]
        cls.stock_location_model = cls.env["stock.location"]
        cls.warehouse_model = cls.env["stock.warehouse"]
        cls.company = cls.env.ref("base.main_company")

        cls.warehouse = cls.warehouse_model.create(
            {
                "name": "Test Warehouse",
                "code": "TW",
                "company_id": cls.company.id,
            }
        )

        cls.product1 = cls.product_model.create(
            {
                "name": "Product 1",
                "company_id": cls.company.id,
                "is_storable": True,
            }
        )
        cls.product2 = cls.product_model.create(
            {
                "name": "Product 2",
                "company_id": cls.company.id,
                "is_storable": True,
            }
        )

        cls.repair_location = cls.stock_location_model.create(
            {
                "name": "Repair Location",
                "usage": "internal",
                "location_id": cls.warehouse.view_location_id.id,
                "company_id": cls.company.id,
            }
        )
        cls.production_location = cls.stock_location_model.create(
            {
                "name": "Production Location",
                "usage": "production",
                "company_id": cls.company.id,
            }
        )

        cls.env["stock.quant"].create(
            {
                "product_id": cls.product1.id,
                "location_id": cls.repair_location.id,
                "quantity": 10,
            }
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product2.id,
                "location_id": cls.warehouse.lot_stock_id.id,
                "quantity": 10,
            }
        )

    def _create_repair_order(self, product):
        return self.repair_model.create(
            {
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "location_id": self.repair_location.id,
                "company_id": self.company.id,
            }
        )

    def _create_picking_and_move(self, repair_order):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": False,
                "user_id": False,
                "picking_type_id": self.warehouse.int_type_id.id,
                "move_type": "direct",
                "location_id": self.repair_location.id,
                "location_dest_id": self.production_location.id,
                "company_id": self.company.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": repair_order.product_id.name,
                "product_id": repair_order.product_id.id,
                "location_id": repair_order.location_id.id,
                "location_dest_id": self.production_location.id,
                "picking_id": picking.id,
                "state": "draft",
                "company_id": picking.company_id.id,
                "picking_type_id": self.warehouse.int_type_id.id,
                "product_uom_qty": 1,
                "product_uom": repair_order.product_id.uom_id.id,
                "related_repair_id": repair_order.id,
            }
        )
        return picking

    def test_compute_pickings(self):
        repair_order = self._create_repair_order(self.product1)
        repair_order._action_repair_confirm()
        repair_order._compute_picking_ids()
        self.assertEqual(len(repair_order.picking_ids), 0)

        self._create_picking_and_move(repair_order)
        repair_order._compute_picking_ids()
        self.assertTrue(repair_order.picking_ids)
        self.assertEqual(len(repair_order.picking_ids), 1)

    def test_action_view_pickings(self):
        repair_order = self._create_repair_order(self.product1)
        repair_order._action_repair_confirm()

        picking = self._create_picking_and_move(repair_order)
        self.assertEqual(picking.picking_type_id, self.warehouse.int_type_id)
        repair_order._compute_picking_ids()

        action = repair_order.action_view_pickings()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "stock.picking")
        self.assertIn("domain", action)
        self.assertEqual(action["domain"], [("id", "in", repair_order.picking_ids.ids)])
        self.assertEqual(len(repair_order.picking_ids), 1)
        self.assertEqual(repair_order.picking_ids[0], picking)
