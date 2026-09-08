from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairOrderFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResPartner = cls.env["res.partner"]
        cls.RepairOrder = cls.env["repair.order"]
        cls.RepairService = cls.env["repair.service"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.Product = cls.env["product.product"]
        cls.Uom = cls.env["uom.uom"]
        cls.partner_1 = cls.ResPartner.create(
            {
                "name": "MY-PARTNER-1",
            }
        )
        # Create a test service product
        cls.service_product = cls.Product.create(
            {
                "name": "Repair Service Product",
                "type": "service",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )

        # Create a test repair order
        cls.repair_order = cls.RepairOrder.create(
            {
                "name": "Test Repair Order",
                "partner_id": cls.partner_1.id,
            }
        )

        # Create a repair service associated with the repair order
        cls.repair_service = cls.RepairService.create(
            {
                "repair_id": cls.repair_order.id,
                "product_id": cls.service_product.id,
                "product_uom_qty": 2.0,
                "product_uom": cls.service_product.uom_id.id,
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

    def test_04_copy_display_name_to_sale_order_line(self):
        # Set a custom description on the repair service
        self.repair_service.display_name = "Custom service description"

        # Create a sale order from the repair order
        self.repair_order.action_create_sale_order()

        # Check that the sale order line exists for the service product
        sale_order_line = self.repair_order.sale_order_id.order_line.filtered(
            lambda line: line.product_id == self.service_product
        )
        self.assertTrue(sale_order_line)

        # Check that the description was copied into the sale order line name
        self.assertEqual(sale_order_line.name, "Custom service description")
