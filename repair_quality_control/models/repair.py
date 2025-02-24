# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from odoo.addons.quality_control_oca.models.qc_trigger_line import _filter_trigger_lines


class RepairOrder(models.Model):
    _inherit = "repair.order"

    inspection_ids = fields.One2many(
        "qc.inspection",
        "repair_id",
        "Inspections",
    )

    auto_generate_qc_inspection = fields.Boolean(
        related="company_id.repair_auto_generate_qc_inspection",
    )
    generate_qc_inspection_state = fields.Selection(
        related="company_id.repair_generate_qc_inspection_state",
    )
    show_button_create_qc_inspection = fields.Boolean(
        compute="_compute_show_button_create_qc_inspection"
    )

    @api.depends(
        "auto_generate_qc_inspection",
        "generate_qc_inspection_state",
        "state",
        "invoice_method",
    )
    def _compute_show_button_create_qc_inspection(self):
        self.show_button_create_qc_inspection = False
        for repair in self.filtered(lambda r: not r.auto_generate_qc_inspection):
            if repair.generate_qc_inspection_state == "confirmed":
                if repair.state == "confirmed":
                    self.show_button_create_qc_inspection = True
                elif repair.state == "ready" and repair.invoice_method == "b4repair":
                    self.show_button_create_qc_inspection = True
            elif (
                repair.generate_qc_inspection_state == "done" and repair.state == "done"
            ):
                self.show_button_create_qc_inspection = True

    def create_qc_inspection(self):
        self.ensure_one()
        inspection_model = self.env["qc.inspection"].sudo()
        qc_trigger = self.sudo().env.ref("repair_quality_control.qc_trigger_repair")
        trigger_lines = set()
        for model in [
            "qc.trigger.product_category_line",
            "qc.trigger.product_template_line",
            "qc.trigger.product_line",
        ]:
            partner = self.partner_id if qc_trigger.partner_selectable else False
            trigger_lines = trigger_lines.union(
                self.env[model]
                .sudo()
                .get_trigger_line_for_product(
                    qc_trigger, ["after"], self.product_id.sudo(), partner=partner
                )
            )
        for trigger_line in _filter_trigger_lines(trigger_lines):
            inspection_model._make_inspection(self, trigger_line)

    def action_repair_confirm(self):
        result = super().action_repair_confirm()
        for rep in self:
            auto_generate = rep.auto_generate_qc_inspection
            if auto_generate and rep.generate_qc_inspection_state == "confirmed":
                rep.create_qc_inspection()
        return result

    def action_repair_done(self):
        result = super().action_repair_done()
        for rep in self:
            auto_generate = rep.auto_generate_qc_inspection
            if auto_generate and rep.generate_qc_inspection_state == "done":
                if rep.invoice_method != "after_repair":
                    rep.create_qc_inspection()
        return result

    def action_repair_invoice_create(self):
        result = super().action_repair_invoice_create()
        for rep in self:
            if rep.state == "done":
                auto_generate = rep.auto_generate_qc_inspection
                if auto_generate and rep.generate_qc_inspection_state == "done":
                    if rep.invoice_method == "after_repair":
                        rep.create_qc_inspection()
        return result

    def action_repair_cancel(self):
        inspections = self.sudo().inspection_ids
        draft_inspections = inspections.filtered(lambda i: i.state == "draft")
        draft_inspections.unlink()
        inspections -= draft_inspections
        inspections.action_cancel()
        return super().action_repair_cancel()

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
            "default_object_id": f"repair.order,{self.id}",
        }
        return action

    def action_view_repair_inspections(self):
        return {
            "name": "Inspections from " + self.name,
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "qc.inspection",
            "domain": [("id", "in", self.inspection_ids.ids)],
        }
