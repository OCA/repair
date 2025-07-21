from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # to be able to group lines by repair in sections
    repair_order_id = fields.Many2one(
        "repair.order",
        copy=False,
    )
