from odoo import models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def action_create_sale_order(self):
        """
        Context flag so that repair lines are automatically synced
        as sale order lines when creating the SO from the Repair Order.
        """
        self = self.with_context(repair_lines_manual_sync=True)
        return super().action_create_sale_order()
