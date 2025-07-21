from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _create_repair_sale_order_line(self):
        res = super()._create_repair_sale_order_line()
        for move in self:
            sale_lines = self.env["sale.order.line"].search(
                [
                    ("move_ids", "in", move.id),
                    (
                        "order_id",
                        "=",
                        move.repair_id.sale_order_id.id
                        if move.repair_id.sale_order_id
                        else False,
                    ),
                ]
            )
            sale_lines.write({"repair_order_id": move.repair_id.id})
        return res
