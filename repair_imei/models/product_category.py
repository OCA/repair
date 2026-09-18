# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    imei_required = fields.Boolean(
        string="IMEI Required",
        default=False,
        help="Set requirement manually, or inherit from parent category.",
    )

    def _get_computed_imei_required(self):
        self.ensure_one()
        if not self.parent_path:
            return self.imei_required or False

        ancestor_ids = [int(p) for p in self.parent_path.split("/") if p]
        ancestors = {
            cat.id: cat for cat in self.env["product.category"].browse(ancestor_ids)
        }
        for catg_id in reversed(ancestor_ids):
            catg = ancestors.get(catg_id)
            if catg and catg.imei_required:
                return True

        return False
