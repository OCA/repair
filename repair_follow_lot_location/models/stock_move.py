# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        done_moves = self.filtered(lambda m: m.state == "done")
        if not done_moves:
            return res
        lots = done_moves.move_line_ids.lot_id
        if not lots:
            return res
        repair_orders = self.env["repair.order"].search(
            [
                ("follow_lot_location", "=", True),
                ("lot_id", "in", lots.ids),
                ("state", "not in", ["done", "cancel"]),
            ]
        )
        if not repair_orders:
            return res
        destination_by_lot = {}
        for move_line in done_moves.move_line_ids:
            destination_by_lot[move_line.lot_id] = move_line.location_dest_id
        for repair_order in repair_orders:
            location = destination_by_lot.get(repair_order.lot_id)
            if location:
                repair_order.location_id = destination_by_lot.get(repair_order.lot_id)
        return res
