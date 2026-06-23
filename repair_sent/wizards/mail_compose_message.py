# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MailComposeMessage(models.TransientModel):

    _inherit = "mail.compose.message"

    def _action_send_mail(self, auto_commit=False):
        res = super()._action_send_mail(auto_commit=auto_commit)
        repair_wizards = self.filtered(lambda w: w.model == "repair.order")
        if repair_wizards:
            repair_orders = self.env["repair.order"].browse(
                repair_wizards.mapped("res_id")
            )
            repair_orders.quotation_sent = True
        return res
