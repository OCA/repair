# pylint: disable=abstract-method
"""Extend product templates for IMEI fields."""

from odoo import api, fields, models


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
        compute="_compute_imei_required",
        store=True,
        readonly=False,
        help="""Set requirement manually, or select 'Use Category Requirement'
         to inherit from product category.""",
    )

    @api.depends("categ_id.imei_required")
    def _compute_imei_required(self):
        for template in self:
            if template.categ_id and template.categ_id.imei_required:
                template.imei_required = "yes"
            else:
                template.imei_required = "no"
