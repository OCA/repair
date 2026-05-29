# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    repair_consumption_step = fields.Boolean(
        string="Enable Repair Consumption Step",
        help="If enabled, consumption moves from repairs will be grouped "
        "in a picking instead of being directly validated.",
    )
    repair_consumption_picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Repair Consumption Picking Type",
        domain="[('code','=','internal'), ('warehouse_id','=', id)]",
        help="Picking type used for repair consumption moves when the extra step is enabled.",
    )
