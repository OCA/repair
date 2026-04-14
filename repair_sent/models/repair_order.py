# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"
    state = fields.Selection(
        selection_add=[("draft",), ("sent", "Quotation Sent"), ("confirmed",)],
        ondelete={"sent": "set draft"},
    )
    quotation_sent = fields.Boolean(readonly=True)

    def write(self, vals):
        res = super().write(vals)
        if vals.get("quotation_sent") and (
            to_update_records := self.filtered(lambda ro: ro.state == "draft")
        ):
            to_update_records.state = "sent"
        return res

    def action_repair_confirm(self):
        """Allow confirming repairs from 'sent' by temporarily shifting state."""
        if sent_repairs := self.filtered(lambda ro: ro.state == "sent"):
            sent_repairs.update({"state": "draft"})
        return super().action_repair_confirm()
