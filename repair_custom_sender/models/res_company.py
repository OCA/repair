# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    use_custom_repair_sender = fields.Boolean(
        string="Use Custom Sender for Repairs",
        help="If checked, repair emails will use the custom address below.",
    )

    repair_custom_email_from = fields.Char(
        string="Repair Custom Email Sender",
        help="The email address that will appear as the sender.",
    )
