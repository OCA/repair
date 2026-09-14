# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_manufacturer = fields.Boolean(
        default=False,
        help="Check if this partner is an OEM or device manufacturer.",
        index=True,
    )
