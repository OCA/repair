# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    repair_group_id = fields.Many2one(
        "repair.group",
        string="Repair Group",
        ondelete="set null",
    )

    def create_repair_group(self):
        self.ensure_one()
        repair_group = self.env["repair.group"].create(
            {
                "partner_id": self.partner_id.id,
                "picking_ids": [(4, self.id)],
            }
        )
        return {
            "name": "Repair Group",
            "type": "ir.actions.act_window",
            "res_model": "repair.group",
            "res_id": repair_group.id,
            "view_mode": "form",
        }

    def action_view_repair_group(self):
        self.ensure_one()
        return {
            "name": "Repair Group",
            "type": "ir.actions.act_window",
            "res_model": "repair.group",
            "res_id": self.repair_group_id.id,
            "view_mode": "form",
        }


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    repair_order_id = fields.Many2one(
        "repair.order",
        string="Repair Order",
        copy=False,
        readonly=True,
    )
