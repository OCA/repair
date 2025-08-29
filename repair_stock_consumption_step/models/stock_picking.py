# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        done_pickings = self.filtered(lambda p: p.state == "done")
        repair_orders = self.env["repair.order"].search(
            [
                ("state", "=", "consumption"),
                ("consumption_picking_id", "in", done_pickings.ids),
            ]
        )
        repair_orders._action_consumption_done()
        return res
