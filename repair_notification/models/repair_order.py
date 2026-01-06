# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RepairOrder(models.Model):

    _inherit = "repair.order"

    repair_start_mail_sent = fields.Boolean(default=False, copy=False)

    def write(self, vals):
        res = super().write(vals)
        if (
            "state" in vals
            and vals["state"] == "under_repair"
            and not self.repair_start_mail_sent
        ):
            self._send_repair_start_confirmation_email()
            self.repair_start_mail_sent = True
        elif "state" in vals and vals["state"] == "done":
            self._send_repair_end_confirmation_email()
        return res

    def _send_repair_start_confirmation_email(self):
        """Send customer notification when the repair is started"""
        for rec in self.filtered("company_id.send_repair_start_confirmation"):
            repair_template_id = rec.company_id.repair_start_template_id.id
            rec.with_context(
                force_send=True,
            ).message_post_with_template(repair_template_id)

    def _send_repair_end_confirmation_email(self):
        """Send customer notification when the repair is ended"""
        for rec in self.filtered("company_id.send_repair_end_confirmation"):
            repair_template_id = rec.company_id.repair_end_template_id.id
            rec.with_context(
                force_send=True,
            ).message_post_with_template(repair_template_id)
