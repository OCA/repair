# Copyright 2024 ForgeFlow (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    repair_auto_generate_qc_inspection = fields.Boolean(
        related="company_id.repair_auto_generate_qc_inspection",
        readonly=False,
    )
    repair_generate_qc_inspection_state = fields.Selection(
        related="company_id.repair_generate_qc_inspection_state",
        readonly=False,
    )
