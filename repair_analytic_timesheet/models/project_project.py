# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Project(models.Model):
    _inherit = "project.project"

    spread_timesheet_cost_on_repair = fields.Boolean(
        string="Spread Timesheet Cost on Repair",
        help="When enabled, timesheet costs from this project will be included "
        "in the analytic distribution when the linked repair order is completed.",
    )
