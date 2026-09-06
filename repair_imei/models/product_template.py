# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    """Product template model inheritance extension."""

    _inherit = "product.template"

    imei_required = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
            ("parent", "Use Category Requirement"),
        ],
        string="IMEI Required",
        default="parent",
        help="""Set requirement manually, or select 'Use Category Requirement'
         to inherit from product category.""",
    )
