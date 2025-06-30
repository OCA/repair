# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    repair_id = fields.Many2one("repair.order")

    def action_view_qc_repair_order(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "repair.order",
            "res_id": self.repair_id.id,
        }

    def action_repair(self):
        self.ensure_one()
        if self.picking_id:
            action = self.picking_id.action_repair_return()
            action["context"].update(
                {
                    "default_product_id": self.product_id.id,
                    "default_lot_id": self.lot_id.id,
                    "default_move_id": self.object_id.id,
                    "default_inspection_ids": [self.id],
                }
            )
            return action
