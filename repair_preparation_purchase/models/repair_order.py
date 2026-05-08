# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class RepairOrder(models.Model):

    _inherit = "repair.order"

    preparation_purchase_ids = fields.Many2many(
        comodel_name="purchase.order", compute="_compute_preparation_purchase_ids"
    )

    preparation_purchase_count = fields.Integer(
        compute="_compute_preparation_purchase_ids"
    )

    @api.depends("operations")
    def _compute_preparation_purchase_ids(self):
        for rec in self:
            rec.preparation_purchase_ids = self.env["purchase.order"].search(
                [("order_line.repair_line_id", "in", rec.operations.ids)]
            )
            rec.preparation_purchase_count = len(rec.preparation_purchase_ids)

    def action_view_preparation_purchase_order(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Preparation Purchase Order(s)"),
            "res_model": self.preparation_purchase_ids._name,
            "domain": [("id", "in", self.preparation_purchase_ids.ids)],
            "view_mode": "tree,form",
            "context": self.env.context,
        }
