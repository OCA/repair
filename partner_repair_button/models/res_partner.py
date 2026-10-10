from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    repair_count = fields.Integer(string="Repairs", compute="_compute_repair_count")

    def _compute_repair_count(self):
        for partner in self:
            partner.repair_count = self.env["repair.order"].search_count(
                [("partner_id", "=", partner.id)]
            )

    def action_view_repairs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Repairs",
            "res_model": "repair.order",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
