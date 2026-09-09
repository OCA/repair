# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    imei_required = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
            ("parent", "Use Category Requirement"),
        ],
        string="IMEI Required",
        default="parent",
        required=True,
        help="Set requirement manually, or inherit from parent category.",
    )

    def _get_computed_imei_required(self):
        """Recursively walk up category parents to resolve 'parent' setting."""
        self.ensure_one()
        val = self.imei_required
        if val == "parent" and self.parent_id:
            return self.parent_id._get_computed_imei_required()
        return val if val in ("yes", "no") else "no"
