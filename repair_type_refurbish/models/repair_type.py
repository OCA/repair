# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RepairType(models.Model):
    _inherit = "repair.type"

    refurbish_location_dest_id = fields.Many2one(
        "stock.location",
        "Refurbish destination Location",
        help="This is the location where the refurbished product will be send",
    )
