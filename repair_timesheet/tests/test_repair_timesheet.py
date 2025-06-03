# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests import Form
from odoo.tests.common import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestRepairOrderTimesheetTotalHours(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.repair_order = cls.env["repair.order"].create(
            {
                "name": "Test Repair Order",
                "product_id": cls.product.id,
                "partner_id": cls.partner.id,
            }
        )

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
            }
        )

        cls.project = cls.env["project.project"].create(
            {
                "name": "Test Project",
            }
        )

    def test_no_timesheets(self):
        """Test total hours when no timesheets are associated"""
        self.assertEqual(
            self.repair_order.timesheet_total_hours,
            0,
            "Total hours should be 0 when there are no timesheets.",
        )

    def test_one_timesheet(self):
        """Test total hours with one timesheet"""
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 5.0,
                "name": "Timesheet 1",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )

        self.repair_order._compute_timesheet_total_hours()

        self.assertEqual(
            self.repair_order.timesheet_total_hours,
            5.0,
            "Total hours should be 5 with one timesheet entry.",
        )

    def test_multiple_timesheets(self):
        """Test total hours with multiple timesheets"""
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 3.0,
                "name": "Timesheet 1",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 2.5,
                "name": "Timesheet 2",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 1.5,
                "name": "Timesheet 3",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )

        self.repair_order._compute_timesheet_total_hours()

        self.assertEqual(
            self.repair_order.timesheet_total_hours,
            7.0,
            "Total hours should be 7 (3 + 2.5 + 1.5) with multiple timesheets.",
        )

    def test_timesheet_update(self):
        """Test updating an existing timesheet"""
        timesheet = self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 3.0,
                "name": "Timesheet to update",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )

        self.repair_order._compute_timesheet_total_hours()
        self.assertEqual(self.repair_order.timesheet_total_hours, 3.0)

        timesheet.unit_amount = 4.5

        self.repair_order._compute_timesheet_total_hours()
        self.assertEqual(
            self.repair_order.timesheet_total_hours,
            4.5,
            "Total hours should update when a timesheet is modified.",
        )

    def test_timesheet_deletion(self):
        """Test deleting a timesheet"""
        timesheet = self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 3.0,
                "name": "Timesheet to delete",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )

        self.repair_order._compute_timesheet_total_hours()
        self.assertEqual(self.repair_order.timesheet_total_hours, 3.0)

        timesheet.unlink()

        self.repair_order._compute_timesheet_total_hours()
        self.assertEqual(
            self.repair_order.timesheet_total_hours,
            0.0,
            "Total hours should be 0 after deleting all timesheets.",
        )

    def test_negative_timesheet_hours(self):
        """Test with negative timesheet hours"""
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": -2.0,
                "name": "Negative Timesheet",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )

        self.repair_order._compute_timesheet_total_hours()
        self.assertEqual(
            self.repair_order.timesheet_total_hours,
            -2.0,
            "Total hours should correctly handle negative values.",
        )

    def test_mixed_positive_negative_hours(self):
        """Test with a mix of positive and negative hours"""
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 5.0,
                "name": "Positive Timesheet",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": -2.0,
                "name": "Negative Timesheet",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )

        self.repair_order._compute_timesheet_total_hours()
        self.assertEqual(
            self.repair_order.timesheet_total_hours,
            3.0,
            "Total hours should be the sum of positive "
            "and negative values (5 - 2 = 3).",
        )

    def test_form_view_timesheet_total(self):
        """Test timesheet total hours in form view context"""
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 2.0,
                "name": "Form View Test 1",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )
        self.env["account.analytic.line"].create(
            {
                "repair_order_id": self.repair_order.id,
                "unit_amount": 3.0,
                "name": "Form View Test 2",
                "employee_id": self.employee.id,
                "project_id": self.project.id,
            }
        )

        with Form(self.repair_order) as repair_form:
            self.assertEqual(
                repair_form.timesheet_total_hours,
                5.0,
                "Total hours should be correctly computed in form view.",
            )
