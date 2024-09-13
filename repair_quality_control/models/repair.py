# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    inspection_ids = fields.One2many(
        "qc.inspection",
        "repair_id",
        "Inspections",
    )

    def action_create_qc_inspection(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "quality_control_oca.action_qc_inspection"
        )
        action["view_mode"] = "form"
        action["views"] = [(False, "form")]
        action["target"] = "current"
        action["name"] = _("Create Inspection")

        action["context"] = {
            "default_qty": self.product_qty,
            "default_repair_id": self.id,
            "default_object_id": f"product.product,{self.product_id.id}",
        }
        if self.lot_id:
            action["context"]["default_object_id"] = f"stock.lot,{self.lot_id.id}"
        return action

    def action_view_repair_inspections(self):
        return {
            "name": "Inspections from " + self.name,
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "qc.inspection",
            "domain": [("id", "in", self.inspection_ids.ids)],
        }
