# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    repair_id = fields.Many2one("repair.order", index="btree_not_null")

    def _action_done(self, cancel_backorder=False):
        repair_moves = self.browse()
        if self.env.context.get("dont_validate_repair_move"):
            repair_moves = self.filtered("repair_id")

        return super(StockMove, self - repair_moves)._action_done(
            cancel_backorder=cancel_backorder
        )
