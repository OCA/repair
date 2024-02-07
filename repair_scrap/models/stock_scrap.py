# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    repair_id = fields.Many2one("repair.order", string="Repair order")

    is_repair_scrap = fields.Boolean(
        default=False,
        copy=False,
        help="This Stock Move has been created from a Scrap operation in Repair.",
    )

    def do_scrap(self):
        res = super(StockScrap, self).do_scrap()
        if self.is_repair_scrap:
            self.move_id.is_repair_scrap = True
        return res

    def _prepare_move_values(self):
        res = super(StockScrap, self)._prepare_move_values()
        res["repair_id"] = self.repair_id.id
        return res

    def action_view_repair_order(self):
        action = self.env.ref("repair.action_repair_order_tree")
        res = self.env.ref("repair.view_repair_order_form", False)
        result = action.sudo().read()[0]
        # choose the view_mode accordingly
        result["views"] = [(res and res.id or False, "form")]
        result["res_id"] = self.repair_id.id
        return result
