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
