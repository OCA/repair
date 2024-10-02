# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    default_product_location_dest_id = fields.Many2one(
        "stock.location",
        "Default Product Destination Location",
        compute="_compute_default_product_location_dest_id",
        check_company=True,
        store=True,
        readonly=False,
        precompute=True,
        help="This is the default product destination location when you create a "
        "repair order with this operation type.",
    )

    @api.depends("code")
    def _compute_default_product_location_dest_id(self):
        for picking_type in self:
            stock_location = picking_type.warehouse_id.lot_stock_id
            if picking_type.code == "repair_operation":
                picking_type.default_product_location_dest_id = stock_location.id
