# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models,fields

class ProductProduct(models.Model):
    _inherit = "product.product"

    is_imei_required = fields.Boolean(
        related = "product_tmpl_id.is_imei_required",
        store=True,
        readonly=True
    )
