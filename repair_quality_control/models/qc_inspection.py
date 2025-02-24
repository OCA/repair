# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QcInspection(models.Model):
    _inherit = "qc.inspection"

    repair_id = fields.Many2one(
        comodel_name="repair.order",
        compute="_compute_repair_id",
        store=True,
    )

    @api.depends("object_id")
    def _compute_repair_id(self):
        self.repair_id = False
        for rec in self:
            if rec.object_id and rec.object_id._name == "repair.order":
                rec.repair_id = rec.object_id

    @api.depends("object_id")
    def _compute_product_id(self):
        result = super()._compute_product_id()
        self.product_id = False
        for rec in self:
            if rec.object_id and rec.object_id._name == "repair.order":
                rec.product_id = rec.object_id.product_id
        return result

    @api.depends("object_id")
    def _compute_lot(self):
        result = super()._compute_lot()
        self.lot_id = False
        for rec in self:
            if rec.object_id and rec.object_id._name == "repair.order":
                rec.lot_id = rec.object_id.lot_id
        return result

    def object_selection_values(self):
        objects = super().object_selection_values()
        objects.append(("repair.order", "Repair Order"))
        return objects

    def action_view_qc_repair_order(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "repair.order",
            "res_id": self.repair_id.id,
        }
