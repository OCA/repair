# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    manufacturer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Manufacturer",
        tracking=True,
        domain=[("is_manufacturer", "=", True)],
        help="Select manufacturer to filter available categories and products.",
    )

    category_id = fields.Many2one(
        comodel_name="product.category",
        string="Product Category",
        help="Filter products by category for the selected manufacturer.",
    )

    allowed_category_ids = fields.Many2many(
        comodel_name="product.category",
        compute="_compute_allowed_category_ids",
        string="Allowed Categories",
    )

    @api.depends("manufacturer_id")
    def _compute_allowed_category_ids(self):
        for repair in self:
            if not repair.manufacturer_id:
                repair.allowed_category_ids = False
                continue

            products = self.env["product.product"].search(
                [("manufacturer_id", "=", repair.manufacturer_id.id)]
            )
            repair.allowed_category_ids = products.mapped("categ_id")

    @api.onchange("manufacturer_id")
    def _onchange_manufacturer_id(self):
        """Reset downstream selections when manufacturer changes."""
        self.category_id = False
        self.product_id = False

    @api.onchange("category_id")
    def _onchange_category_id(self):
        """Reset product selection when category changes."""
        self.product_id = False
