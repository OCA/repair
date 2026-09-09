# Copyright 2026 Escodoo - Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    repair_timesheet_default_project_id = fields.Many2one(
        related="company_id.repair_timesheet_default_project_id",
        domain=[("allow_timesheets", "=", True)],
        readonly=False,
    )
    repair_timesheet_default_task_id = fields.Many2one(
        related="company_id.repair_timesheet_default_task_id",
        domain="[('project_id', '=', repair_timesheet_default_project_id)]",
        readonly=False,
    )

    @api.onchange("repair_timesheet_default_project_id")
    def _onchange_repair_timesheet_default_project_id(self):
        if (
            self.repair_timesheet_default_task_id.project_id
            != self.repair_timesheet_default_project_id
        ):
            self.repair_timesheet_default_task_id = False
