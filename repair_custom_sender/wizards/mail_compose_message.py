# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def _action_send_mail(self, auto_commit=False):
        company = self.env.company
        use_custom_sender = company.use_custom_repair_sender
        custom_sender_email = company.repair_custom_email_from

        if (
            use_custom_sender
            and custom_sender_email
            and (repair_wizards := self.filtered(lambda w: w.model == "repair.order"))
        ):
            repair_wizards.write({"email_from": custom_sender_email})

        return super()._action_send_mail(auto_commit=auto_commit)
