from odoo import models


class RepairService(models.Model):
    _inherit = "repair.service"

    def _prepare_sale_order_line_vals(self, product_qty):
        res = super()._prepare_sale_order_line_vals(product_qty)
        res.update(
            {
                "repair_order_id": self.repair_id.id,
            }
        )
        return res
