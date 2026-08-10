# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    timesheet_ids = fields.One2many(domain=[("project_id", "!=", False)])

    def action_view_analytic_lines(self):
        result = super().action_view_analytic_lines()
        result["domain"] = [
            ("repair_order_id", "=", self.id),
            ("project_id", "=", False),
        ]
        return result

    def _compute_analytic_line_count(self):
        for repair in self:
            repair.analytic_line_count = self.env["account.analytic.line"].search_count(
                [("repair_order_id", "=", repair.id), ("project_id", "=", False)]
            )

    def _prepare_analytic_line_vals_for_timesheet(self, timesheet):
        if not self.analytic_distribution:
            return []

        vals_list = []
        for account_ids_str, percentage in self.analytic_distribution.items():
            account_field_values = {}
            account_ids = [
                int(a) for a in account_ids_str.split(",") if a.strip().isdigit()
            ]
            for account in (
                self.env["account.analytic.account"].browse(account_ids).exists()
            ):
                account_field_values[account.plan_id._column_name()] = account.id
            if not account_field_values:
                continue

            vals_list.append(
                {
                    "name": self.name,
                    "date": fields.Date.context_today(self),
                    "unit_amount": timesheet.unit_amount,
                    "amount": timesheet.amount * float(percentage) / 100.0,
                    "employee_id": timesheet.employee_id.id
                    if timesheet.employee_id
                    else False,
                    "company_id": self.company_id.id,
                    "repair_order_id": self.id,
                    **account_field_values,
                }
            )
        return vals_list

    def _create_analytic_lines(self):
        res = super()._create_analytic_lines()
        all_vals = []
        for repair in self.filtered("analytic_distribution"):
            timesheets = repair.timesheet_ids.filtered(
                lambda t: t.project_id.spread_timesheet_cost_on_repair
            )
            for timesheet in timesheets:
                all_vals.extend(
                    repair._prepare_analytic_line_vals_for_timesheet(timesheet)
                )
        if all_vals:
            self.env["account.analytic.line"].sudo().create(all_vals)
        self.invalidate_recordset(["analytic_line_count"])
        return res

    def _delete_analytic_lines(self):
        self.env["account.analytic.line"].sudo().search(
            [("repair_order_id", "in", self.ids), ("project_id", "=", False)]
        ).unlink()
        self.invalidate_recordset(["analytic_line_count"])
