# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    send_repair_start_confirmation = fields.Boolean(
        related="company_id.send_repair_start_confirmation",
        readonly=False,
    )
    repair_start_template_id = fields.Many2one(
        related="company_id.repair_start_template_id",
        readonly=False,
    )
    send_repair_end_confirmation = fields.Boolean(
        related="company_id.send_repair_end_confirmation",
        readonly=False,
    )
    repair_end_template_id = fields.Many2one(
        related="company_id.repair_end_template_id",
        readonly=False,
    )
