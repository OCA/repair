# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"
    manufacturer_id = fields.Many2one(
        comodel_name="res.partner",
        domain="[('is_manufacturer','=',True)]",
        string="Product Manufacturer",
        help="Device manufacturer or OEM brand (e.g., Apple, Samsung, Xiaomi)",
    )
