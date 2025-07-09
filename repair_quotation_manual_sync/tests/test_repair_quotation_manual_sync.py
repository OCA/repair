from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairQuotationManualSync(TransactionCase):
    def setUp(self):
        super().setUp()
        self.RepairOrder = self.env["repair.order"]
        self.SaleOrder = self.env["sale.order"]
        self.Product = self.env["product.product"]
        self.StockLocation = self.env["stock.location"]
        self.Partner = self.env.ref("base.res_partner_1")
        self.location = self.StockLocation.create({"name": "Test Location"})

        # Create a stockable product instead of a service
        self.product = self.Product.create(
            {
                "name": "Repair Product",
                "type": "product",
                "invoice_policy": "order",
                "list_price": 100.0,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

        self.repair_order = self.RepairOrder.create(
            {
                "name": "Test Repair",
                "partner_id": self.Partner.id,
            }
        )

        self.move = self.repair_order.move_ids.create(
            {
                "name": "Repair Line",
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product.uom_id.id,
                "repair_id": self.repair_order.id,
                "location_id": self.location.id,
                "location_dest_id": self.location.id,
                "repair_line_type": "add",
            }
        )

    def test_01_invoiceable_syncs_to_sale_order(self):
        self.assertTrue(self.move.repair_invoiceable)
        self.repair_order.action_create_sale_order()
        sale_order = self.repair_order.sale_order_id
        self.assertTrue(sale_order)
        self.assertEqual(len(sale_order.order_line), 1)
        self.assertEqual(sale_order.order_line.product_id, self.product)

    def test_02_non_invoiceable_line_not_synced(self):
        self.move.repair_invoiceable = False
        self.repair_order.action_create_sale_order()
        sale_order = self.repair_order.sale_order_id
        self.assertTrue(sale_order)
        self.assertFalse(sale_order.order_line)

    def test_03_sale_order_shows_sync_banner(self):
        self.repair_order.action_create_sale_order()
        sale_order = self.repair_order.sale_order_id
        self.assertFalse(sale_order.needs_repair_sync)
        self.move.product_uom_qty = 2.0
        sale_order._compute_needs_repair_sync()
        self.assertTrue(sale_order.needs_repair_sync)

    def test_04_action_sync_repair_lines(self):
        self.repair_order.action_create_sale_order()
        sale_order = self.repair_order.sale_order_id
        self.move.product_uom_qty = 2.0
        sale_order.action_sync_repair_lines()
        line = sale_order.order_line
        self.assertEqual(line.product_uom_qty, 2.0)

    def test_05_confirmed_sale_order_blocks_invoiceable_change(self):
        self.repair_order.action_create_sale_order()
        self.repair_order.sale_order_id.action_confirm()
        self.assertTrue(self.move.is_repair_sale_confirmed)
