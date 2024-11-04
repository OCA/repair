from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairOrderFlow(TransactionCase):
    def setUp(self):
        super().setUp()
        self.RepairOrder = self.env["repair.order"]
        self.RepairService = self.env["repair.service"]
        self.SaleOrder = self.env["sale.order"]
        self.Product = self.env["product.product"]
        self.Uom = self.env["uom.uom"]

        # Create a test service product
        self.service_product = self.Product.create(
            {
                "name": "Repair Service Product",
                "type": "service",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

        # Create a test repair order
        self.repair_order = self.RepairOrder.create(
            {
                "name": "Test Repair Order",
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )

        # Create a repair service associated with the repair order
        self.repair_service = self.RepairService.create(
            {
                "repair_id": self.repair_order.id,
                "product_id": self.service_product.id,
                "product_uom_qty": 2.0,
                "product_uom": self.service_product.uom_id.id,
            }
        )

    def test_01_action_create_sale_order(self):
        # Create a sale order from the repair order
        self.repair_order.action_create_sale_order()

        # Check that the sale order has been created
        sale_order = self.repair_order.sale_order_id
        self.assertTrue(sale_order)

        # Check that the sale order has a line for the repair service
        sale_order_line = sale_order.order_line.filtered(
            lambda lam: lam.product_id == self.service_product
        )
        self.assertTrue(sale_order_line)

        # Check that the sale order line has the correct quantity
        self.assertEqual(sale_order_line.product_uom_qty, 2.0)

    def test_02_action_create_sale_order_under_warranty(self):
        # Set the repair order to be under warranty
        self.repair_order.under_warranty = True

        # Create a sale order from the repair order
        self.repair_order.action_create_sale_order()

        # Check that the sale order has been created
        sale_order = self.repair_order.sale_order_id
        self.assertTrue(sale_order)

        # Check that the sale order has a line for the repair service
        sale_order_line = sale_order.order_line.filtered(
            lambda lam: lam.product_id == self.service_product
        )
        self.assertTrue(sale_order_line)

        # Check that the sale order line has the correct quantity
        self.assertEqual(sale_order_line.product_uom_qty, 2.0)

        # Check that the sale order line has a price unit of 0.0
        self.assertEqual(sale_order_line.price_unit, 0.0)

    def test_03_action_create_sale_order_not_under_warranty(self):
        # Set the repair order to be not under warranty
        self.repair_order.under_warranty = False

        # Create a sale order from the repair order
        self.repair_order.action_create_sale_order()

        # Check that the sale order has been created
        sale_order = self.repair_order.sale_order_id
        self.assertTrue(sale_order)

        # Check that the sale order has a line for the repair service
        sale_order_line = sale_order.order_line.filtered(
            lambda lam: lam.product_id == self.service_product
        )
        self.assertTrue(sale_order_line)

        # Check that the sale order line has the correct quantity
        self.assertEqual(sale_order_line.product_uom_qty, 2.0)

        # Check that the sale order line has the correct price unit
        self.assertEqual(sale_order_line.price_unit, self.service_product.lst_price)
