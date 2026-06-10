# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):

    _inherit = "stock.move"

    repair_line_id = fields.Many2one(
        comodel_name="repair.line", ondelete="cascade", readonly=True
    )

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        if self.repair_line_id:
            res["repair_line_id"] = self.repair_line_id.id
        return res

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for rec in self:
            if not rec.repair_line_id or not rec.state == "done":
                continue
            vals = {}
            move_lines = rec.move_line_ids
            lot_id = move_lines.lot_id[0].id if move_lines.lot_id else False
            vals["lot_id"] = lot_id
            location_id = (
                move_lines.location_dest_id[0].id
                if move_lines.location_dest_id
                else rec.location_dest_id.id
            )
            if location_id:
                vals["location_id"] = location_id
            rec.repair_line_id.write(vals)
        return res
