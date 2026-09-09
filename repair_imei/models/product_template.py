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
        for template in self:
            val = template.imei_required
            if val == "parent" and template.categ_id:
                val = template.categ_id._get_computed_imei_required()

            template.is_imei_required = val == "yes"
