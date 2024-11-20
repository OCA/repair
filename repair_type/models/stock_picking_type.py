# Copyright (C) 2024 APSL-Nagarro Antoni Marroig
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    default_remove_location_src_id = fields.Many2one(
        "stock.location",
        "Default Remove Source Location",
        compute="_compute_default_location_src_id",
        check_company=True,
        store=True,
        readonly=False,
        precompute=True,
        help="This is the default remove source location when you create a repair "
        "order with this operation type.",
    )
    default_recycle_location_src_id = fields.Many2one(
        "stock.location",
        "Default Recycle Source Location",
        compute="_compute_default_location_src_id",
        check_company=True,
        store=True,
        readonly=False,
        precompute=True,
        help="This is the default recycle source location when you create a repair "
        "order with this operation type.",
    )
    default_add_location_src_id = fields.Many2one(
        "stock.location",
        "Default Add Source Location",
        compute="_compute_default_location_src_id",
        check_company=True,
        store=True,
        readonly=False,
        precompute=True,
        help="This is the default add source location when you create a repair "
        "order with this operation type.",
    )

    @api.depends("code")
    def _compute_default_location_src_id(self):
        res = super()._compute_default_location_src_id()
        for picking_type in self:
            stock_location = picking_type.warehouse_id.lot_stock_id
            if picking_type.code == "repair_operation":
                picking_type.default_add_location_src_id = stock_location.id
                picking_type.default_remove_location_src_id = stock_location.id
                picking_type.default_recycle_location_src_id = stock_location.id
        return res
