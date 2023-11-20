# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    scrap_count = fields.Integer(compute="_compute_scrap_count", string="# Scrap")

    scrap_ids = fields.One2many("stock.scrap", "repair_id")

    def _compute_scrap_count(self):
        for order in self:
            order.scrap_count = len(order.scrap_ids)

    def action_view_scrap_transfers(self):
        self.ensure_one()
        action = self.env.ref("stock.action_stock_scrap")
        result = action.sudo().read()[0]
        scraps = self.env["stock.scrap"].search([("origin", "=", self.name)])
        if len(scraps) > 1:
            result["domain"] = [("id", "in", scraps.ids)]
        elif len(scraps) == 1:
            res = self.env.ref("stock.stock_scrap_form_view", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = scraps.ids[0]
        return result
