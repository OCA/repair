from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    repair_service_ids = fields.One2many(
        comodel_name="repair.service",
        inverse_name="sale_line_id",
    )
