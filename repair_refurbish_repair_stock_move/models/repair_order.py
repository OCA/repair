# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def create_refurbished_stock_move(self):
        self.ensure_one()
        move = self.env["stock.move"].create(self._get_refurbish_stock_move_dict())
        move.quantity_done = self.product_qty
        self.refurbish_move_id = move.id

    def _create_and_confirm_stock_moves(self):
        res = super()._create_and_confirm_stock_moves()
        # if the repair order is started the action assign needs to be called
        for rec in self.filtered(lambda l: l.state == "under_repair"):
            moves = rec.mapped("stock_move_ids")
            moves.filtered(lambda l: l.state == "confirmed")._action_assign()
        return res

    def write(self, values):
        res = super().write(values)
        for repair in self:
            if "to_refurbish" in values.keys():
                if repair.mapped("stock_move_ids") and repair.state not in (
                    "draft",
                    "done",
                    "cancel",
                ):
                    # recreate stock moves
                    repair.mapped("stock_move_ids")._action_cancel()
                    repair._create_and_confirm_stock_moves()
            if "refurbish_lot_id" in values.keys():
                if repair.mapped("stock_move_ids") and repair.state not in (
                    "draft",
                    "done",
                    "cancel",
                ):
                    # assign new lot
                    repair.mapped("stock_move_ids.move_line_ids").filtered(
                        lambda l: l.product_id == repair.refurbish_product_id
                    ).lot_id = repair.refurbish_lot_id.id
        return res

    def _prepare_repair_stock_move(self):
        res = super()._prepare_repair_stock_move()
        if not self.to_refurbish:
            return res
        else:
            self.create_refurbished_stock_move()
            res.update({"location_dest_id": self.location_dest_id.id})
        return res

    def action_repair_end(self):
        res = super().action_repair_end()
        for r in self.filtered(lambda l: l.to_refurbish):
            r.refurbish_move_id._action_done()
        return res

    def action_open_stock_moves(self):
        res = super().action_open_stock_moves()
        if self.refurbish_move_id:
            all_move_ids = self.mapped("stock_move_ids").ids + [
                self.refurbish_move_id.id
            ]
            res.update({"domain": [("id", "in", all_move_ids)]})
        return res
