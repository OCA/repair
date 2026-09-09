# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairAnalyticDistributionTimesheet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.analytic_plan = cls.env["account.analytic.plan"].create(
            {"name": "Test Repair Timesheet Plan"}
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "Test Repair Timesheet Account", "plan_id": cls.analytic_plan.id}
        )
        cls.analytic_distribution = {str(cls.analytic_account.id): 100.0}

        cls.product_to_repair = cls.env["product.product"].create(
            {"name": "Product To Repair TS", "type": "consu"}
        )

        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.repair_type = cls.warehouse.repair_type_id

        cls.employee = cls.env["hr.employee"].create(
            {"name": "Test Technician", "hourly_cost": 50.0}
        )
        cls.project_spread = cls.env["project.project"].create(
            {
                "name": "Repair Project (spread=True)",
                "spread_timesheet_cost_on_repair": True,
            }
        )
        cls.project_no_spread = cls.env["project.project"].create(
            {
                "name": "Repair Project (spread=False)",
                "spread_timesheet_cost_on_repair": False,
            }
        )

    def _make_repair(self):
        return self.env["repair.order"].create(
            {
                "product_id": self.product_to_repair.id,
                "picking_type_id": self.repair_type.id,
                "analytic_distribution": self.analytic_distribution,
            }
        )

    def _add_timesheet(self, repair, project, hours=2.0, date=None):
        """`amount` is not settable directly: hr_timesheet recomputes it
        from `unit_amount * employee_id.hourly_cost` on create/write
        (see `hr_timesheet.models.hr_timesheet._timesheet_postprocess_values`),
        overriding any value passed here. `cls.employee.hourly_cost` is
        fixed at 50.0, so the resulting amount is always `-hours * 50.0`.
        """
        return self.env["account.analytic.line"].create(
            {
                "name": "Work on repair",
                "repair_order_id": repair.id,
                "project_id": project.id,
                "employee_id": self.employee.id,
                "unit_amount": hours,
                "company_id": repair.company_id.id,
                **({"date": date} if date else {}),
            }
        )

    def _complete_repair(self, repair):
        repair._action_repair_confirm()
        repair.action_repair_start()
        repair.action_repair_end()

    def _distribution_lines(self, repair):
        return self.env["account.analytic.line"].search(
            [("repair_order_id", "=", repair.id), ("project_id", "=", False)]
        )

    def test_timesheet_with_spread_creates_analytic_line(self):
        """Completing a repair creates analytic lines for timesheets with spread."""
        repair = self._make_repair()
        self._add_timesheet(repair, self.project_spread, hours=2.0)
        self._complete_repair(repair)

        lines = self._distribution_lines(repair)
        self.assertTrue(lines, "Expected analytic distribution line from timesheet.")
        self.assertAlmostEqual(
            sum(lines.mapped("amount")),
            -100.0,
            places=2,
            msg="Total amount should match the timesheet cost.",
        )

    def test_timesheet_without_spread_skipped(self):
        """Timesheets from projects with spread=False are not distributed."""
        repair = self._make_repair()
        self._add_timesheet(repair, self.project_no_spread, hours=2.0)
        self._complete_repair(repair)

        lines = self._distribution_lines(repair)
        self.assertFalse(
            lines, "No analytic distribution lines expected when spread=False."
        )

    def test_timesheet_amount_respects_distribution_percentage(self):
        """With 60/40 split, each account gets its proportional timesheet cost."""
        second_account = self.env["account.analytic.account"].create(
            {"name": "Second TS Account", "plan_id": self.analytic_plan.id}
        )
        distribution = {
            str(self.analytic_account.id): 60.0,
            str(second_account.id): 40.0,
        }
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product_to_repair.id,
                "picking_type_id": self.repair_type.id,
                "analytic_distribution": distribution,
            }
        )
        self._add_timesheet(repair, self.project_spread, hours=3.0)
        self._complete_repair(repair)

        lines = self._distribution_lines(repair)
        self.assertEqual(len(lines), 2)

        primary = lines.filtered(
            lambda line: line[self.analytic_plan._column_name()]
            == self.analytic_account
        )
        secondary = lines.filtered(
            lambda line: line[self.analytic_plan._column_name()] == second_account
        )
        # unit_amount * employee_id.hourly_cost = 3.0 * 50.0 = 150.0 total
        self.assertAlmostEqual(primary.amount, -90.0, places=2)
        self.assertAlmostEqual(secondary.amount, -60.0, places=2)

    def test_prepare_analytic_line_vals_for_timesheet_edge_cases(self):
        """No distribution line is created for a timesheet when either:
        - the repair has no analytic_distribution set
          (`if not self.analytic_distribution: return []`), or
        - the distribution key only references non-existent accounts,
          so no plan column can be resolved
          (`if not account_field_values: continue`).
        """
        cases = [
            ("no_analytic_distribution", False),
            ("only_nonexistent_accounts", {"999999999": 100.0}),
        ]
        for case, distribution in cases:
            with self.subTest(case=case):
                repair = self.env["repair.order"].create(
                    {
                        "product_id": self.product_to_repair.id,
                        "picking_type_id": self.repair_type.id,
                        "analytic_distribution": distribution,
                    }
                )
                self._add_timesheet(repair, self.project_spread, hours=2.0)
                self._complete_repair(repair)

                self.assertFalse(
                    self._distribution_lines(repair),
                    f"No distribution line expected for case '{case}'.",
                )

    def test_cancel_removes_distribution_lines_but_preserves_timesheets(self):
        """Cancel deletes distribution lines but keeps timesheet entries intact.

        Core repair.order forbids cancelling an order that's already
        'done', so this cannot go through _complete_repair() first (as
        repair_analytic's own equivalent cancel test also avoids doing).
        A distribution line is seeded directly to exercise the deletion
        behavior of _delete_analytic_lines() from the draft state.
        """
        repair = self._make_repair()
        timesheet = self._add_timesheet(repair, self.project_spread, hours=1.0)
        self.env["account.analytic.line"].sudo().create(
            {
                "name": repair.name,
                "repair_order_id": repair.id,
                "company_id": repair.company_id.id,
                self.analytic_plan._column_name(): self.analytic_account.id,
            }
        )

        repair.action_repair_cancel()

        self.assertFalse(
            self._distribution_lines(repair),
            "Distribution lines must be removed on cancel.",
        )
        self.assertTrue(
            timesheet.exists(),
            "Timesheet entry must be preserved on cancel.",
        )

    def test_analytic_line_count_excludes_timesheets(self):
        """analytic_line_count counts only distribution lines, not timesheets."""
        repair = self._make_repair()
        self._add_timesheet(repair, self.project_spread, hours=1.0)
        self._complete_repair(repair)

        distribution_count = len(self._distribution_lines(repair))
        self.assertEqual(repair.analytic_line_count, distribution_count)

    def test_timesheet_ids_excludes_distribution_lines(self):
        """timesheet_ids (Timesheets tab / total hours) must not pick up
        the part-consumption / cost distribution lines created for the
        repair order, only genuine timesheet entries (project_id set)."""
        repair = self._make_repair()
        timesheet = self._add_timesheet(repair, self.project_spread, hours=2.0)
        self._complete_repair(repair)

        self.assertIn(timesheet, repair.timesheet_ids)
        distribution_lines = self._distribution_lines(repair)
        self.assertTrue(distribution_lines)
        self.assertFalse(set(distribution_lines.ids) & set(repair.timesheet_ids.ids))

    def test_action_view_analytic_lines_domain_excludes_timesheets(self):
        """The 'Analytic Lines' smart button must show the same records it
        counts: distribution lines only, not raw timesheet entries."""
        repair = self._make_repair()
        self._add_timesheet(repair, self.project_spread, hours=2.0)
        self._complete_repair(repair)

        action = repair.action_view_analytic_lines()
        self.assertIn(("project_id", "=", False), action["domain"])

    def test_distribution_line_keeps_timesheet_date(self):
        """The distribution line must be booked on the date the work was
        done, not on the date the repair happened to be completed.
        Otherwise the cost lands in the wrong accounting period whenever
        a repair spans a period boundary."""
        repair = self._make_repair()
        timesheet = self._add_timesheet(
            repair, self.project_spread, hours=2.0, date="2024-01-15"
        )
        self._complete_repair(repair)

        lines = self._distribution_lines(repair)
        self.assertTrue(lines)
        self.assertEqual(
            lines.mapped("date"),
            [timesheet.date] * len(lines),
            "Distribution line must inherit the timesheet date.",
        )

    def test_distribution_line_keeps_timesheet_uom(self):
        """unit_amount is a number of hours, so the line must carry the
        timesheet's UoM; without it the quantity is unitless and analytic
        reports cannot aggregate it."""
        repair = self._make_repair()
        timesheet = self._add_timesheet(repair, self.project_spread, hours=2.0)
        self._complete_repair(repair)

        lines = self._distribution_lines(repair)
        self.assertTrue(lines)
        self.assertTrue(timesheet.product_uom_id)
        self.assertEqual(
            lines.product_uom_id,
            timesheet.product_uom_id,
            "Distribution line must inherit the timesheet UoM.",
        )
