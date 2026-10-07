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

    inherit_imei_required = fields.Boolean(
        string="Inherit IMEI Required",
        default=True,
        help="If checked, the category will inherit the IMEI requirement "
        "from its parent chain.If unchecked, the value in *IMEI Required* "
        "is used even if a parent forces it.",
    )

    def _get_computed_imei_required(self):
        self.ensure_one()
        if not self.parent_path or not self.inherit_imei_required:
            return self.imei_required

        ancestor_ids = [int(p) for p in self.parent_path.split("/") if p]
        ancestors = {
            cat.id: cat for cat in self.env["product.category"].browse(ancestor_ids)
        }
        for catg_id in reversed(ancestor_ids):
            catg = ancestors.get(catg_id)
            if catg and catg.imei_required:
                return True

        return self.imei_required

    def write(self, vals):
        """
        If imei_required or inherit_imei_required changes, we must
        trigger a recompute for all products in this category and
        all its sub-categories.
        """
        res = super().write(vals)
        if "imei_required" in vals or "inherit_imei_required" in vals:
            categories = self.search([("id", "child_of", self.ids)])
            templates = self.env["product.template"].search(
                [("categ_id", "in", categories.ids)]
            )
            templates.modified(["is_imei_required"])
        return res
