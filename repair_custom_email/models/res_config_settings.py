# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    use_custom_repair_email = fields.Boolean(
        related="company_id.use_custom_repair_email",
        readonly=False,
    )

    custom_repair_email = fields.Char(
        related="company_id.custom_repair_email",
        readonly=False,
    )
