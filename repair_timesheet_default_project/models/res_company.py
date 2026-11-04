# Copyright 2026 Escodoo - Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    repair_timesheet_default_project_id = fields.Many2one(
        "project.project",
        string="Default Project for Repair Timesheets",
        domain=[("allow_timesheets", "=", True)],
    )
    repair_timesheet_default_task_id = fields.Many2one(
        "project.task",
        string="Default Task for Repair Timesheets",
        domain="[('project_id', '=', repair_timesheet_default_project_id)]",
    )
