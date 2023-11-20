# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RepairType(models.Model):
    _inherit = "repair.type"

    scrap_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Scrap Destination Location",
    )
