# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
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
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.company
        cls.draft_state = cls.env["ir.model.fields.selection"].search(
            [
                ("field_id.model", "=", "repair.order"),
                ("field_id.name", "=", "state"),
                ("value", "=", "draft"),
            ],
            limit=1,
        )
        cls.company.write(
            {
                "add_grouped_repair_state_ids": [
                    Command.set(cls.draft_state.ids),
                ],
            }
        )
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
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )

        repair.action_add_another_repair()
        group = repair.group_id

        self.assertTrue(group.name)
        self.assertEqual(group.partner_id, self.partner)
        self.assertEqual(group.repair_count, 2)

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

        # Test changing partner
        repair1.write({"partner_id": self.another_partner.id})

        self.assertEqual(repair1.partner_id, self.another_partner)
        self.assertEqual(repair2.partner_id, self.another_partner)
        self.assertEqual(group.partner_id, self.another_partner)

        # Test clearing partner
        repair1.write({"partner_id": False})
        self.assertFalse(repair1.partner_id)
        self.assertFalse(repair2.partner_id)
        self.assertFalse(group.partner_id)

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
        repair2.action_validate()
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
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        action = repair1.action_create_sale_order()
        sale_order = self.env["sale.order"].browse(action["res_id"])

        self.assertEqual(repair1.sale_order_id, sale_order)
        self.assertEqual(repair2.sale_order_id, sale_order)

        # Main assertion: SO was created and repairs are linked
        # Order lines depend on additional materials, not main products
        self.assertTrue(sale_order)

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
        """Test that repairs with existing SO raise error when selected."""
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
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        repair1.action_create_sale_order()

        self.assertTrue(repair1.sale_order_id)
        self.assertTrue(repair2.sale_order_id)
        self.assertEqual(repair1.sale_order_id, repair2.sale_order_id)

        with self.assertRaises(UserError):
            repair1.action_create_sale_order()

        repair3 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )
        with self.assertRaises(UserError):
            (repair1 + repair3).action_create_sale_order()

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

        # Test skip_group_sync
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

        group2 = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair3 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group2.id,
            }
        )
        repair4 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group2.id,
            }
        )

        repair3.with_context(skip_group_confirm=True)._action_repair_confirm()
        self.assertEqual(repair4.state, "draft")

        group3 = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair5 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group3.id,
            }
        )
        repair6 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group3.id,
            }
        )

        repair5.action_validate()
        repair5._action_repair_confirm()
        repair6.action_validate()
        repair6._action_repair_confirm()

        repair5.with_context(skip_group_cancel=True).action_repair_cancel()
        self.assertEqual(repair6.state, "confirmed")

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

    def test_12_group_sale_order_creation_with_multiple_warehouses(self):
        """RO from the same group with different warehouses create separate SOs."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        # Create second warehouse and picking type
        warehouse_2 = self.env["stock.warehouse"].create(
            {
                "name": "Second Warehouse",
                "code": "WH_TEST_2",
            }
        )
        picking_type_2 = self.env["stock.picking.type"].create(
            {
                "name": "Test Repair Operation 2",
                "code": "repair_operation",
                "sequence_code": "REP2",
                "warehouse_id": warehouse_2.id,
            }
        )

        # Two repairs with first warehouse
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,  # Warehouse 1
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,  # Warehouse 1
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        # One repair with second warehouse
        repair3 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type_2.id,  # Warehouse 2
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        # Trigger grouped SO creation
        repair1.action_create_sale_order()

        # Each repair must be linked to a sale order
        self.assertTrue(repair1.sale_order_id)
        self.assertTrue(repair2.sale_order_id)
        self.assertTrue(repair3.sale_order_id)

        # Repairs with the same warehouse share the same SO
        self.assertEqual(repair1.sale_order_id, repair2.sale_order_id)

        # Repair with different warehouse has a different SO
        self.assertNotEqual(repair1.sale_order_id, repair3.sale_order_id)

        # Sanity check: group has exactly two distinct sale orders
        sale_orders = group.repair_ids.mapped("sale_order_id")
        self.assertEqual(len(sale_orders), 2)

    def test_13_empty_group_so_creation(self):
        """Test SO creation for group with no valid repairs."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Create cancelled repair (not valid for SO)
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
                "state": "cancel",
            }
        )

        # Should not create SO and not raise error
        repair.action_create_sale_order()
        self.assertFalse(repair.sale_order_id)

    def test_14_mixed_repair_states_in_group(self):
        """Test cascade actions with mixed repair states."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
                "state": "draft",
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
                "state": "confirmed",  # Already confirmed
            }
        )

        # Should only confirm draft repairs
        repair1._action_repair_confirm()
        self.assertEqual(repair1.state, "confirmed")
        self.assertEqual(repair2.state, "confirmed")  # Should remain confirmed

    def test_15_warehouse_none_handling(self):
        """Test SO creation with repairs where warehouse is None."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Use existing picking type but simulate None warehouse
        # by mocking the warehouse_id to be None/False
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                "group_id": group.id,
            }
        )

        # Temporarily set warehouse to None to test the logic
        original_warehouse = self.picking_type.warehouse_id
        self.picking_type.warehouse_id = False

        try:
            repair.action_create_sale_order()
            self.assertTrue(repair.sale_order_id)
            self.assertFalse(repair.sale_order_id.warehouse_id)
        finally:
            # Restore original warehouse
            self.picking_type.warehouse_id = original_warehouse

    def test_16_partner_sync_complex_scenarios(self):
        """Test partner synchronization in complex scenarios."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        repairs = self.env["repair.order"].create(
            [
                {
                    "partner_id": self.partner.id,
                    "picking_type_id": self.picking_type.id,
                    "group_id": group.id,
                }
                for _ in range(5)
            ]
        )

        # Test bulk partner change
        repairs[0].write({"partner_id": self.another_partner.id})

        # All should have new partner
        for repair in repairs:
            self.assertEqual(repair.partner_id, self.another_partner)

    def test_17_empty_recordset_handling(self):
        """Test methods with empty recordsets."""
        # Test empty recordset in _action_repair_confirm
        empty_repairs = self.env["repair.order"]
        result = empty_repairs._action_repair_confirm()
        self.assertTrue(result)  # Should return True for empty recordset

        # Test empty recordset in action_repair_cancel
        result = empty_repairs.action_repair_cancel()
        self.assertTrue(result)  # Should return True for empty recordset

    def test_18_no_partner_error_multiple_repairs(self):
        """Test no partner error with multiple repairs."""
        repairs = self.env["repair.order"].create(
            [
                {
                    "picking_type_id": self.picking_type.id,
                    "product_id": self.product.id,
                    # No partner_id - should raise error
                }
                for _ in range(3)
            ]
        )

        with self.assertRaises(UserError) as context:
            repairs.action_create_sale_order()

        self.assertIn("define a customer", str(context.exception))

    def test_19_valid_ungrouped_repairs(self):
        """Test SO creation for valid ungrouped repairs."""
        # Create ungrouped repairs (no group_id)
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                # No group_id - should use standard logic
            }
        )
        repair2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "product_id": self.product.id,
                # No group_id - should use standard logic
            }
        )

        # Test each repair individually to avoid multiple SOs in action
        repair1.action_create_sale_order()
        repair2.action_create_sale_order()

        # Both should have SOs created
        self.assertTrue(repair1.sale_order_id)
        self.assertTrue(repair2.sale_order_id)
        # They should have different SOs since they're ungrouped
        self.assertNotEqual(repair1.sale_order_id, repair2.sale_order_id)

    def test_20_empty_repairs_to_process(self):
        """Test partner sync when no repairs to process."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Single repair in group - no other repairs to sync with
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        # Should not crash when no grouped_repair_ids
        repair.write({"partner_id": self.another_partner.id})
        self.assertEqual(repair.partner_id, self.another_partner)

    def test_21_cascade_empty_group_repairs(self):
        """Test cascade actions when group has no other repairs."""
        group = self.env["repair.order.group"].create({"partner_id": self.partner.id})

        # Only one repair in group
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        # Should work fine even with no other repairs in group
        repair.action_validate()
        repair._action_repair_confirm()
        self.assertEqual(repair.state, "confirmed")

        repair.action_repair_cancel()
        self.assertEqual(repair.state, "cancel")

    # ------------------------------------------------------------------ #
    #  Tests for task 5417: configurable "Add Grouped Repair" visibility  #
    # ------------------------------------------------------------------ #

    def _set_allowed_states(self, *state_codes):
        """Configure states where Add Grouped Repair is allowed."""
        states = self.env["ir.model.fields.selection"].search(
            [
                ("field_id.model", "=", "repair.order"),
                ("field_id.name", "=", "state"),
                ("value", "in", list(state_codes)),
            ]
        )
        self.company.write(
            {
                "add_grouped_repair_state_ids": [
                    Command.set(states.ids),
                ],
            }
        )

    def _create_repair(self):
        """Create a draft repair order with the default test partner."""
        return self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product.id,
                "picking_type_id": self.picking_type.id,
            }
        )

    def _create_part_move(self, repair, product=None):
        """Create an added part move for a repair order."""
        product = product or self.product
        return self.env["stock.move"].create(
            {
                "name": product.display_name,
                "company_id": repair.company_id.id,
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": 1.0,
            }
        )

    def test_22_add_grouped_repair_visible_in_default_draft_state(self):
        """Button is visible in draft state with default configuration."""
        repair = self._create_repair()

        self.assertEqual(repair.state, "draft")
        self.assertTrue(repair.show_add_grouped_repair)
        self.assertTrue(repair._can_add_grouped_repair())

    def test_23_add_grouped_repair_hidden_in_disallowed_state(self):
        """Button is hidden when current repair state is not configured."""
        self._set_allowed_states("draft")

        repair = self._create_repair()
        repair._action_repair_confirm()

        self.assertEqual(repair.state, "confirmed")
        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_24_add_grouped_repair_hidden_when_sale_order_confirmed(self):
        """Confirmed sale order blocks adding grouped repairs."""
        self._set_allowed_states("draft", "confirmed", "under_repair")

        repair = self._create_repair()
        sale_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        sale_order.action_confirm()
        repair.sale_order_id = sale_order

        self.assertEqual(sale_order.state, "sale")
        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_25_add_grouped_repair_hidden_when_sale_order_cancelled(self):
        """Cancelled sale order blocks adding grouped repairs."""
        self._set_allowed_states("draft", "confirmed", "under_repair")

        repair = self._create_repair()
        sale_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        sale_order.action_cancel()
        repair.sale_order_id = sale_order

        self.assertEqual(sale_order.state, "cancel")
        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_26_add_grouped_repair_hidden_when_no_state_is_allowed(self):
        """Button is hidden when all state settings are disabled."""
        self._set_allowed_states()

        repair = self._create_repair()

        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_27_add_grouped_repair_visible_in_confirmed_state_when_allowed(self):
        """Button is visible in confirmed state when it is configured."""
        self._set_allowed_states("draft", "confirmed")

        repair = self._create_repair()
        repair._action_repair_confirm()

        self.assertEqual(repair.state, "confirmed")
        self.assertTrue(repair.show_add_grouped_repair)
        self.assertTrue(repair._can_add_grouped_repair())

    def test_28_add_grouped_repair_action_raises_when_not_allowed(self):
        """Backend guard prevents adding grouped repairs when not allowed."""
        self._set_allowed_states()

        repair = self._create_repair()

        with self.assertRaises(UserError):
            repair.action_add_another_repair()

        self.assertFalse(repair.show_add_grouped_repair)
        self.assertFalse(repair._can_add_grouped_repair())

    def test_29_add_grouped_repair_action_creates_repair_when_allowed(self):
        """Backend action creates a grouped repair when rules allow it."""
        self._set_allowed_states("draft")

        repair = self._create_repair()
        action = repair.action_add_another_repair()
        new_repair = self.env["repair.order"].browse(action["res_id"])

        self.assertTrue(repair.group_id)
        self.assertEqual(new_repair.group_id, repair.group_id)
        self.assertEqual(new_repair.partner_id, repair.partner_id)

    def test_30_default_grouped_repair_state_is_draft(self):
        """New companies use draft as default Add Grouped Repair state."""
        company = self.env["res.company"].create(
            {
                "name": "Grouped Repair Default Company",
            }
        )

        self.assertEqual(
            company.add_grouped_repair_state_ids.mapped("value"),
            ["draft"],
        )

    def test_31_add_grouped_repair_action_reuses_existing_group(self):
        """Adding grouped repair reuses an existing repair group."""
        self._set_allowed_states("draft")

        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        action = repair.action_add_another_repair()
        new_repair = self.env["repair.order"].browse(action["res_id"])

        self.assertEqual(repair.group_id, group)
        self.assertEqual(new_repair.group_id, group)
        self.assertEqual(group.repair_count, 2)

    def test_32_grouped_sale_order_creation_requires_partner(self):
        """Grouped quotation creation raises when grouped repair has no partner."""
        group = self.env["repair.order.group"].create({})
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )

        with self.assertRaises(UserError) as error:
            repair.action_create_sale_order()

        self.assertIn("define a customer", str(error.exception))
        self.assertIn(repair.name, str(error.exception))

    def test_33_link_to_existing_group_sale_order_returns_false_without_so(self):
        """Existing quotation helper returns False when repairs have no open SO."""
        self._set_allowed_states("draft")

        repair = self._create_repair()
        action = repair.action_add_another_repair()
        new_repair = self.env["repair.order"].browse(action["res_id"])

        self.assertFalse((repair | new_repair)._link_to_existing_group_sale_order())
        self.assertFalse(repair.sale_order_id)
        self.assertFalse(new_repair.sale_order_id)

    def test_34_reuse_open_group_quotation_for_new_repair_parts(self):
        """New grouped repair reuses open quotation and keeps old parts."""
        self._set_allowed_states("draft")

        repair = self._create_repair()
        first_move = self._create_part_move(repair)

        repair.action_create_sale_order()
        sale_order = repair.sale_order_id

        self.assertTrue(sale_order)
        self.assertEqual(first_move.sale_line_id.order_id, sale_order)

        action = repair.action_add_another_repair()
        new_repair = self.env["repair.order"].browse(action["res_id"])

        second_product = self.env["product.product"].create(
            {
                "name": "Second Grouped Repair Part",
                "type": "consu",
                "list_price": 50.0,
            }
        )
        second_move = self._create_part_move(new_repair, second_product)

        new_repair.action_create_sale_order()

        repair.invalidate_recordset()
        new_repair.invalidate_recordset()
        sale_order.invalidate_recordset()
        first_move.invalidate_recordset()
        second_move.invalidate_recordset()

        self.assertEqual(repair.sale_order_id, sale_order)
        self.assertEqual(new_repair.sale_order_id, sale_order)
        self.assertEqual(first_move.sale_line_id.order_id, sale_order)
        self.assertEqual(second_move.sale_line_id.order_id, sale_order)
        self.assertIn(self.product, sale_order.order_line.product_id)
        self.assertIn(second_product, sale_order.order_line.product_id)

    def test_35_existing_group_sale_order_without_repairs_to_add(self):
        """Existing quotation helper succeeds when all repairs already have SO."""
        repair = self._create_repair()
        self._create_part_move(repair)

        repair.action_create_sale_order()

        self.assertTrue(repair.sale_order_id)
        self.assertTrue(repair._link_to_existing_group_sale_order())

    def test_36_link_to_existing_group_sale_order_raises_for_multiple_sos(self):
        """Existing quotation helper rejects multiple open SOs in one group."""
        group = self.env["repair.order.group"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        repair_1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        repair_2 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product.id,
                "picking_type_id": self.picking_type.id,
                "group_id": group.id,
            }
        )
        sale_order_1, sale_order_2 = self.env["sale.order"].create(
            [
                {
                    "partner_id": self.partner.id,
                },
                {
                    "partner_id": self.partner.id,
                },
            ]
        )

        repair_1.sale_order_id = sale_order_1
        repair_2.sale_order_id = sale_order_2

        with self.assertRaises(UserError) as error:
            (repair_1 | repair_2)._link_to_existing_group_sale_order()

        self.assertIn("Several open sale orders", str(error.exception))
        self.assertIn(repair_1.name, str(error.exception))
        self.assertIn(repair_2.name, str(error.exception))
