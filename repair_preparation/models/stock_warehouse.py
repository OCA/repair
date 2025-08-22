# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    repair_preparation_enabled = fields.Boolean(
        string="Enable Repair Preparation",
        help="If disabled for this warehouse, no preparation procurements/pickings "
        "will be created for its repairs and finishing repairs won't enforce "
        "preparation checks.",
    )
    repair_preparation_picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Default Preparation Operation Type",
        domain="[('code','=','internal'), ('warehouse_id','=', id)]",
        help="Default internal transfer operation type to bring spare parts from "
        "Stock to the Preparation area for repairs in this warehouse.",
    )
