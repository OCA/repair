# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    timesheet_ids = fields.One2many(
        "account.analytic.line", "repair_order_id", string="Timesheets"
    )
    timesheet_total_hours = fields.Float(
        string="Total Hours",
        compute="_compute_timesheet_total_hours",
        store=True,
        help="Total hours spent on this repair order.",
    )

    @api.depends("timesheet_ids.unit_amount")
    def _compute_timesheet_total_hours(self):
        for order in self:
            order.timesheet_total_hours = sum(order.timesheet_ids.mapped("unit_amount"))
