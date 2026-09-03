# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Add repair group settings to the Repair configuration page."""

    _inherit = "res.config.settings"

    add_grouped_repair_state_ids = fields.Many2many(
        related="company_id.add_grouped_repair_state_ids",
        readonly=False,
    )
