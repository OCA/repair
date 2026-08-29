# pylint: disable=abstract-method
"""Extend product categories for IMEI tracking configuration."""

from odoo import fields, models


class ProductCategory(models.Model):
    """ "Inherited Product category tracking model context."""

    _inherit = "product.category"

    imei_required = fields.Boolean(
        string="IMEI Required",
        help="Enforce IMEI assignment for all products under this category.",
    )
