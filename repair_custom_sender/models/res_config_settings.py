# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    use_custom_repair_sender = fields.Boolean(
        related="company_id.use_custom_repair_sender",
        readonly=False,
    )

    repair_custom_email_from = fields.Char(
        related="company_id.repair_custom_email_from",
        readonly=False,
    )
