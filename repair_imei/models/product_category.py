# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    imei_required = fields.Boolean(
        string="IMEI Required",
        default=False,
        required=True,
        help="Set requirement manually, or inherit from parent category.",
    )

    def _get_computed_imei_required(self):
        """Recursively walk up category parents to resolve 'parent' setting.

        Resolution order:
        1. Checks the current category's 'imei_required' value.
        2. If the current value is False and a parent category exists,
           it recursively checks the parent's value.
        3. Continues bubbling up the hierarchy until it finds a True value
           or reaches the top of the category tree.
        """
        self.ensure_one()
        val = self.imei_required
        if not val and self.parent_id:
            return self.parent_id._get_computed_imei_required()
        return val if val else False
