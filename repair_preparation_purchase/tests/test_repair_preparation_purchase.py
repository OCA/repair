# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairPreparationPurchase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "test partner"})
        cls.vendor = cls.env["res.partner"].create({"name": "test vendor"})

        cls.product = cls.env["product.product"].create(
            {"name": "product to repair", "type": "product"}
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "product to consume", "type": "product"}
        )
        cls.product_c_2 = cls.env["product.product"].create(
            {"name": "product to consume 2", "type": "product"}
        )
        cls.env["product.supplierinfo"].create(
            {
                "partner_id": cls.vendor.id,
                "product_tmpl_id": cls.product_c.product_tmpl_id.id,
                "price": 1.0,
                "min_qty": 1.0,
            }
        )
        cls.env["product.supplierinfo"].create(
            {
                "partner_id": cls.vendor.id,
                "product_tmpl_id": cls.product_c_2.product_tmpl_id.id,
                "price": 1.0,
                "min_qty": 1.0,
            }
        )

        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "WH", "code": "wh_test"}
        )
        cls.stock_loc = cls.warehouse.lot_stock_id
        cls.in_type = cls.warehouse.in_type_id
        cls.prep_loc = cls.env["stock.location"].create(
            {
                "name": "Preparation",
                "usage": "internal",
                "location_id": cls.stock_loc.id,
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.prep_type = cls.env["stock.picking.type"].create(
            {
                "name": "Preparation",
                "code": "internal",
                "warehouse_id": cls.warehouse.id,
                "sequence_code": "PREP",
                "default_location_src_id": cls.stock_loc.id,
                "default_location_dest_id": cls.prep_loc.id,
            }
        )
        cls.warehouse.write(
            {
                "repair_preparation_enabled": True,
                "repair_preparation_picking_type_id": cls.prep_type.id,
            }
        )

        # Pull from Stock -> Preparation, but as MTO to propagate upstream procurement
        cls.prep_route = cls.env["stock.route"].create(
            {
                "name": "Route to Preparation (MTO)",
                "product_selectable": True,
                "warehouse_selectable": False,
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.prep_rule = cls.env["stock.rule"].create(
            {
                "name": "Pull to Preparation (MTO)",
                "route_id": cls.prep_route.id,
                "action": "pull",
                "procure_method": "make_to_order",
                "picking_type_id": cls.prep_type.id,
                "location_src_id": cls.stock_loc.id,
                "location_dest_id": cls.prep_loc.id,
                "warehouse_id": cls.warehouse.id,
            }
        )

        # Route: Buy to Stock (so the upstream procurement buys what is missing)
        cls.buy_route = cls.env["stock.route"].create(
            {
                "name": "Buy to WH Stock",
                "product_selectable": True,
                "warehouse_selectable": False,
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.buy_rule = cls.env["stock.rule"].create(
            {
                "name": "Buy to Stock",
                "route_id": cls.buy_route.id,
                "action": "buy",
                "warehouse_id": cls.warehouse.id,
                "location_dest_id": cls.stock_loc.id,
                "picking_type_id": cls.in_type.id,
            }
        )

        (cls.product_c + cls.product_c_2).route_ids += cls.prep_route + cls.buy_route
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.prep_loc, 1.0
        )

        cls.repair = cls.env["repair.order"].create(
            {
                "partner_id": cls.partner.id,
                "product_id": cls.product.id,
                "location_id": cls.prep_loc.id,
                "priority": "1",
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.line = cls._create_repair_line(cls.product_c)

    @classmethod
    def _create_repair_line(cls, product):
        return cls.env["repair.line"].create(
            {
                "name": "replace product",
                "repair_id": cls.repair.id,
                "type": "add",
                "price_unit": 100,
                "product_id": product.id,
                "product_uom_qty": 2.0,
            }
        )

    @classmethod
    def _get_available_qty(cls, product, location):
        return cls.env["stock.quant"]._get_available_quantity(product, location)

    def test_validate_runs_procurement_creates_purchase(self):
        self.repair.action_validate()
        self.assertEqual(self.repair.state, "confirmed")
        self.assertTrue(self.line.preparation_move_ids)
        self.assertTrue(self.repair.preparation_picking_ids)
        self.assertTrue(self.repair.preparation_purchase_ids)
        po = self.repair.preparation_purchase_ids
        po_line = po.order_line
        self.assertTrue(po)
        self.assertTrue(po_line)
        self.assertEqual(po_line.product_id, self.line.product_id)
        self.assertEqual(po_line.product_uom_qty, self.line.product_uom_qty)

    def test_create_new_line_under_repair_triggers_procurement(self):
        self.test_validate_runs_procurement_creates_purchase()
        self.repair.action_repair_start()
        self.assertEqual(self.repair.state, "under_repair")
        po = self.repair.preparation_purchase_ids
        po_line = po.order_line
        new_line = self._create_repair_line(self.product_c_2)
        self.assertTrue(new_line.preparation_move_ids)
        self.assertEqual(len(po.order_line), 2)
        new_po_line = po.order_line - po_line
        self.assertEqual(new_po_line.product_id, new_line.product_id)
        self.assertEqual(new_po_line.product_uom_qty, new_line.product_uom_qty)

    def test_modify_ro_line_under_repair_updates_po(self):
        self.test_validate_runs_procurement_creates_purchase()
        self.repair.action_repair_start()
        self.assertEqual(self.repair.state, "under_repair")
        self.assertEqual(len(self.repair.preparation_purchase_ids), 1)
        self.assertEqual(self.repair.preparation_purchase_ids.state, "draft")

        self.repair.operations.product_uom_qty += 1
        self.repair.invalidate_recordset(["preparation_purchase_ids"])
        self.assertEqual(len(self.repair.preparation_purchase_ids), 2)
        self.assertRecordValues(
            self.repair.preparation_purchase_ids.sorted(key="state"),
            [{"state": "cancel"}, {"state": "draft"}],
        )
        po = self.repair.preparation_purchase_ids.filtered(
            lambda po: po.state == "draft"
        )
        self.assertEqual(po.order_line.product_uom_qty, 3)

        self.repair.operations.product_uom_qty -= 1
        self.repair.invalidate_recordset(["preparation_purchase_ids"])
        self.assertEqual(len(self.repair.preparation_purchase_ids), 3)
        self.assertRecordValues(
            self.repair.preparation_purchase_ids.sorted(key="state"),
            [{"state": "cancel"}, {"state": "cancel"}, {"state": "draft"}],
        )
        po = self.repair.preparation_purchase_ids.filtered(
            lambda po: po.state == "draft"
        )
        self.assertEqual(po.order_line.product_uom_qty, 2)
