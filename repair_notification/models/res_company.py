# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    def _default_repair_start_template(self):
        try:
            return self.env.ref(
                "repair_notification.mail_template_repair_start_notification"
            ).id
        except ValueError:
            return False

    def _default_repair_end_template(self):
        try:
            return self.env.ref(
                "repair_notification.mail_template_repair_end_notification"
            ).id
        except ValueError:
            return False

    send_repair_start_confirmation = fields.Boolean(
        help="Notify the customer when repairing starts"
    )
    send_repair_end_confirmation = fields.Boolean(
        help="Notify the customer when repairing ends"
    )
    repair_start_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template confirmation for repair start",
        domain="[('model', '=', 'repair.order')]",
        default=_default_repair_start_template,
        help="Email sent to the customer once the repair is started.",
    )
    repair_end_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template confirmation for repair end",
        domain="[('model', '=', 'repair.order')]",
        default=_default_repair_end_template,
        help="Email sent to the customer once the repair is ended.",
    )
