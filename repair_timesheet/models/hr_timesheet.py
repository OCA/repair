# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    repair_order_id = fields.Many2one(
        "repair.order",
        string="Related Repair Order",
        help="The repair order related to this timesheet entry.",
    )
