# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairOrderGroup(TransactionCase):
    """Test cases for Repair Order Group functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.another_partner = cls.env["res.partner"].create(
            {"name": "Another Customer"}
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )

        cls.picking_type = cls.env["stock.picking.type"].search(
            [("code", "=", "repair_operation"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        if not cls.picking_type:
            warehouse = cls.env["stock.warehouse"].search([], limit=1)
            cls.picking_type = cls.env["stock.picking.type"].create(
                {
                    "name": "Test Repair Operation",
                    "code": "repair_operation",
                    "sequence_code": "REP",
                    "warehouse_id": warehouse.id,
                }
            )

    def test_01_create_repair_order_group(self):
        """Test creating repair order group."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.assertTrue(group.name)
        self.assertEqual(group.partner_id, self.partner)
        self.assertEqual(group.repair_count, 0)

    def test_02_add_another_repair_action(self):
        """Test adding another repair to group."""
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
            }
        )
        self.assertFalse(repair1.group_id)

        action = repair1.action_add_another_repair()
        repair2 = self.env["repair.order"].browse(action["res_id"])

        self.assertTrue(repair1.group_id)
        self.assertEqual(repair1.group_id, repair2.group_id)
        self.assertEqual(repair1.partner_id, repair2.partner_id)
        self.assertIn(repair2, repair1.grouped_repair_ids)
        self.assertEqual(repair1.group_id.repair_count, 2)

    def test_03_partner_synchronization(self):
        """Test partner synchronization across group."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair1.write({"partner_id": self.another_partner.id})

        self.assertEqual(repair1.partner_id, self.another_partner)
        self.assertEqual(repair2.partner_id, self.another_partner)
        self.assertEqual(repair1.group_id.partner_id, self.another_partner)

    def test_04_cascade_confirmation(self):
        """Test cascade confirmation of group repairs."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair1.action_validate()
        repair1._action_repair_confirm()

        self.assertEqual(repair1.state, "confirmed")
        self.assertEqual(repair2.state, "confirmed")

    def test_05_cascade_cancellation(self):
        """Test cascade cancellation of group repairs."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair1.action_validate()
        repair1._action_repair_confirm()
        repair2.action_validate()
        repair2._action_repair_confirm()

        repair1.action_repair_cancel()

        self.assertEqual(repair1.state, "cancel")
        self.assertEqual(repair2.state, "cancel")

    def test_06_group_sale_order_creation(self):
        """Test creating sale order for entire group."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "product_qty": 2.0,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "product_qty": 3.0,
                "group_id": group.id,
            }
        )

        Move = self.env["stock.move"]
        Move.create(
            {
                "name": "Repair1 add",
                "company_id": self.company.id,
                "repair_id": repair1.id,
                "repair_line_type": "add",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 2.0,
            }
        )
        Move.create(
            {
                "name": "Repair2 add",
                "company_id": self.company.id,
                "repair_id": repair2.id,
                "repair_line_type": "add",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 3.0,
            }
        )

        action = repair1.action_create_sale_order()
        sale_order = self.env["sale.order"].browse(action["res_id"])

        self.assertEqual(repair1.sale_order_id, sale_order)
        self.assertEqual(repair2.sale_order_id, sale_order)
        self.assertEqual(len(sale_order.order_line), 2)

        total_qty = sum(sale_order.order_line.mapped("product_uom_qty"))
        self.assertEqual(total_qty, 5.0)  # 2 + 3

    def test_07_warranty_pricing(self):
        """Test warranty pricing in sale order lines."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "under_warranty": True,
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair.write({"sale_order_id": sale_order.id})

        move = self.env["stock.move"].create(
            {
                "name": "Warranty add",
                "company_id": self.company.id,
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1.0,
            }
        )
        move._create_repair_sale_order_line()
        self.assertTrue(sale_order.order_line)

        order_line = sale_order.order_line[0]
        self.assertEqual(order_line.price_unit, 0.0)

    def test_08_prevent_multiple_sale_orders(self):
        """Test preventing multiple sale orders for same group."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        Move = self.env["stock.move"]
        Move.create(
            {
                "name": "First add",
                "company_id": self.company.id,
                "repair_id": repair1.id,
                "repair_line_type": "add",
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1.0,
            }
        )
        repair1.action_create_sale_order()

        with self.assertRaises(UserError):
            repair2.action_create_sale_order()

    def test_09_no_partner_error(self):
        """Test error when creating sale order without partner."""
        repair = self.env["repair.order"].create(
            {
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
            }
        )
        with self.assertRaises(UserError):
            repair.action_create_sale_order()

    def test_10_skip_context_flags(self):
        """Test context flags to prevent recursion."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair1.with_context(skip_group_sync=True).write(
            {"partner_id": self.another_partner.id}
        )
        self.assertEqual(repair2.partner_id, self.partner)

        repair3 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair4 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        repair3.with_context(skip_group_confirm=True)._action_repair_confirm()
        self.assertEqual(repair4.state, "draft")

    def test_11_repair_count_computation(self):
        """Test repair count computation in groups."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.assertEqual(group.repair_count, 0)

        for _ in range(3):
            self.env["repair.order"].create(
                {
                    "partner_id": self.partner.id,
                    "picking_type_id": self.picking_type.id,
                    "group_id": group.id,
                }
            )
        self.assertEqual(group.repair_count, 3)

    def test_12_sequence_generation(self):
        """Test sequence generation for repair groups."""
        group1 = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        group2 = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.assertNotEqual(group1.name, group2.name)
        self.assertNotEqual(group1.name, "New")
        self.assertNotEqual(group2.name, "New")

    def test_13_repair_without_group(self):
        """Test repair order without group works normally."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
            }
        )
        self.assertFalse(repair.group_id)
        repair.action_validate()
        repair._action_repair_confirm()
        self.assertEqual(repair.state, "confirmed")
