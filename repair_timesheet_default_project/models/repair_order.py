# Copyright 2026 Escodoo - Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    repair_timesheet_default_project_id = fields.Many2one(
        related="company_id.repair_timesheet_default_project_id",
    )
    repair_timesheet_default_task_id = fields.Many2one(
        related="company_id.repair_timesheet_default_task_id",
    )
