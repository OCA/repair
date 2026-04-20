# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def _action_send_mail(self, auto_commit=False):
        company = self.env.company
        use_custom_email = company.use_custom_repair_email
        custom_repair_email = company.custom_repair_email

        if (
            use_custom_email
            and custom_repair_email
            and (repair_wizards := self.filtered(lambda w: w.model == "repair.order"))
        ):
            repair_wizards.write({"email_from": custom_repair_email})
            self = self.with_context(custom_repair_email=custom_repair_email)

        return super(MailComposeMessage, self)._action_send_mail(
            auto_commit=auto_commit
        )
