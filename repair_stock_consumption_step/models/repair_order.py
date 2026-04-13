# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models


class RepairOrder(models.Model):

    _inherit = "repair.order"

    consumption_picking_id = fields.Many2one(
        "stock.picking", string="Consumption Picking", readonly=True, copy=False
    )
    repair_consumption_step = fields.Boolean(
        related="warehouse_id.repair_consumption_step"
    )
    state = fields.Selection(
        # Put "consumption" step before "done" step (for UI)
        selection_add=[("consumption", "Waiting Consumption"), ("done",)],
        ondelete={"consumption": "set done"},
    )

    def action_view_consumption_picking(self):
        self.ensure_one()
        return {
            "name": "Repair Consumption Picking",
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "view_mode": "form",
            "res_id": self.consumption_picking_id.id,
        }

    def action_repair_done(self):
        need_consumption_step = self.filtered("repair_consumption_step")
        res = super(RepairOrder, self - need_consumption_step).action_repair_done()
        for rec in need_consumption_step:
            rec_res = super(
                RepairOrder, rec.with_context(dont_validate_repair_move=True)
            ).action_repair_done()
            res.update(rec_res)
            moves = self.env["stock.move"].search([("repair_id", "=", rec.id)])
            if not moves:
                continue
            picking = self.env["stock.picking"].create(
                {
                    "picking_type_id": rec.warehouse_id.repair_consumption_picking_type_id.id,
                    "origin": rec.name,
                    "move_ids": [Command.set(moves.ids)],
                }
            )

            # Preserve lot info before unlink the move lines
            move_id_lots_ids_map = {}
            for move in moves:
                move_id_lots_ids_map[move.id] = move.move_line_ids.mapped("lot_id").ids

            moves.move_line_ids.unlink()
            moves._action_confirm()
            # need exists because confirm() may merge moves
            moves.exists()._action_assign()

            # Reset lot_id on the new move lines
            for move in moves:
                lot_ids = move_id_lots_ids_map.get(move.id)
                if not lot_ids:
                    continue
                for line in move.move_line_ids:
                    if not line.lot_id:
                        line.lot_id = lot_ids.pop(0)

            rec.consumption_picking_id = picking
            rec.state = "consumption"
        return res

    def action_repair_end(self):
        super().action_repair_end()
        need_consumption_step = self.filtered("consumption_picking_id")
        need_consumption_step.state = "consumption"
        return True

    def _action_consumption_done(self):
        for rec in self:
            state = "done"
            if not rec.invoice_id and rec.invoice_method == "after_repair":
                state = "2binvoiced"
            rec.state = state
