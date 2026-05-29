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
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": _("Repair Orders"),
            "res_model": "repair.order",
            "context": self.env.context,
        }

        repair_ids = self.repair_ids.ids
        if len(repair_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": repair_ids[0],
                }
            )
        else:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", repair_ids)],
                }
            )

        return action
