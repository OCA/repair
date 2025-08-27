# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    repair_ids = fields.Many2many(
        comodel_name="repair.order", compute="_compute_repair_ids"
    )
    count_repair = fields.Integer(compute="_compute_repair_ids")

    @api.depends("order_line.repair_line_id")
    def _compute_repair_ids(self):
        for rec in self:
            rec.repair_ids = rec.order_line.repair_line_id.repair_id
            rec.count_repair = len(rec.repair_ids)

    def action_view_repair_order(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Repair Order(s)"),
            "res_model": self.repair_ids._name,
            "domain": [("id", "in", self.repair_ids.ids)],
            "view_mode": "tree,form",
            "context": self.env.context,
        }
