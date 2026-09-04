# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    """ "Inherited Product category tracking model context."""

    _inherit = "product.category"

    imei_required = fields.Boolean(
        string="IMEI Required",
        help="Enforce IMEI assignment for all products under this category.",
    )
