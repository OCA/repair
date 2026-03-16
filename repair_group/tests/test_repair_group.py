# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairGroup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu"}
        )
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.location_dest = cls.env.ref("stock.stock_location_customers")

    def _create_done_picking(self):
        """Helper: create and validate a stock picking."""
        picking_type = self.env.ref("stock.picking_type_out")
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": self.location.id,
                "location_dest_id": self.location_dest.id,
                "owner_id": self.partner.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.location.id,
                            "location_dest_id": self.location_dest.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        for ml in picking.move_line_ids:
            ml.qty_done = ml.reserved_qty
        picking.button_validate()
        return picking

    def test_repair_group_creation(self):
        """Test that a repair group is created with a sequential name."""
        group = self.env["repair.group"].create({"partner_id": self.partner.id})
        self.assertTrue(group.name.startswith("RG/"), "Name should start with RG/")
        self.assertEqual(group.state, "draft")

    def test_action_create_all_repairs(self):
        """Test that repairs are created from picking move lines."""
        picking = self._create_done_picking()
        group = self.env["repair.group"].create(
            {
                "partner_id": self.partner.id,
                "picking_ids": [(4, picking.id)],
            }
        )
        group.action_create_all_repairs()
        self.assertEqual(group.state, "repairs_created")
        self.assertTrue(
            group.repair_order_ids, "Repair orders should have been created"
        )
        self.assertEqual(len(group.repair_order_ids), len(picking.move_line_ids))

    def test_action_return_to_draft(self):
        """Test that repairs are cancelled when returning to draft."""
        picking = self._create_done_picking()
        group = self.env["repair.group"].create(
            {
                "partner_id": self.partner.id,
                "picking_ids": [(4, picking.id)],
            }
        )
        group.action_create_all_repairs()
        self.assertEqual(group.state, "repairs_created")
        group.action_return_to_draft()
        self.assertEqual(group.state, "draft")

    def test_action_request_quotations(self):
        """Test state transition to quotation_requested."""
        picking = self._create_done_picking()
        group = self.env["repair.group"].create(
            {
                "partner_id": self.partner.id,
                "picking_ids": [(4, picking.id)],
            }
        )
        group.action_create_all_repairs()
        group.action_request_quotations()
        self.assertEqual(group.state, "quotation_requested")

    def test_action_end_repair_group_not_done_raises(self):
        """Test that ending a group with unfinished repairs raises UserError."""
        picking = self._create_done_picking()
        group = self.env["repair.group"].create(
            {
                "partner_id": self.partner.id,
                "picking_ids": [(4, picking.id)],
            }
        )
        group.action_create_all_repairs()
        group.write({"state": "under_repair"})
        with self.assertRaises(UserError):
            group.action_end_repair_group()

    def test_stock_picking_create_repair_group(self):
        """Test creating a repair group directly from a stock picking."""
        picking = self._create_done_picking()
        action = picking.create_repair_group()
        self.assertEqual(action["res_model"], "repair.group")
        group = self.env["repair.group"].browse(action["res_id"])
        self.assertTrue(group.exists())
        self.assertIn(picking, group.picking_ids)
        self.assertEqual(group.partner_id, self.partner)

    def test_repair_order_request_approval_no_group_raises(self):
        """Test that requesting approval without a group raises UserError."""
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product.id,
                "partner_id": self.partner.id,
            }
        )
        with self.assertRaises(UserError):
            repair.action_request_approval()
