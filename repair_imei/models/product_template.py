# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Product template model inheritance extension."""

    _inherit = "product.template"

    imei_required = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
            ("parent", "Use Category Strategy"),
        ],
        string="IMEI Required",
        default="parent",
        help="Set requirement manually, or "
        "select 'Use Category Requirement' "
        "to inherit from product category.",
    )

    is_imei_required = fields.Boolean(
        compute="_compute_is_imei_required",
        store=True,
    )

    @api.depends(
        "imei_required",
        "categ_id",
        "categ_id.imei_required",
        "categ_id.parent_id",
    )
    def _compute_is_imei_required(self):
        """Compute whether IMEI tracking is required for the product.

        By default, 'is_imei_required' is set to False.
        1. It first checks the 'imei_required' field at the product level.
           If set to 'yes', it sets 'is_imei_required' to True.
        2. If set to 'parent', it calls the '_get_computed_imei_required'
           function on the product category to traverse the hierarchy
           and resolve the requirement value.
        """
        for template in self:
            val = template.imei_required
            template.is_imei_required = False
            if val == "yes":
                template.is_imei_required = True
            elif val == "parent" and template.categ_id:
                template.is_imei_required = (
                    template.categ_id._get_computed_imei_required()
                )
