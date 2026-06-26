# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    analytic_price_type = fields.Selection(
        selection=[("price", "Price"), ("cost", "Cost")],
        default="price",
    )
