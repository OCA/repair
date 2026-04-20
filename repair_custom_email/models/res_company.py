# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    use_custom_repair_email = fields.Boolean(
        string="Use Custom Email for Repairs",
        help="If enabled, emails sent from Repair Orders will bypass the standard "
        "catchall alias. This forces both the 'From' and 'Reply-To' headers "
        "to use the custom address defined below.",
    )

    custom_repair_email = fields.Char(
        help="The specific email address to be used for all repair-related outgoing "
        "messages. Warning: If this address is not managed by Odoo, customer "
        "replies will be sent to this mailbox instead of the Odoo chatter.",
    )
