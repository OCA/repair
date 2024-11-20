# Copyright (C) 2024 APSL-Nagarro Antoni Marroig
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_repair_locations(self, repair_line_type, repair_id=False):
        res = super()._get_repair_locations(repair_line_type, repair_id)
        if not repair_id:
            if (
                repair_line_type == "add"
                and self.repair_id.picking_type_id.default_add_location_src_id
            ):
                res = (
                    self.repair_id.picking_type_id.default_add_location_src_id,
                    res[1],
                )
            elif (
                repair_line_type == "remove"
                and self.repair_id.picking_type_id.default_remove_location_src_id
            ):
                res = (
                    self.repair_id.picking_type_id.default_remove_location_src_id,
                    res[1],
                )
            elif (
                repair_line_type == "recycle"
                and self.repair_id.picking_type_id.default_recycle_location_src_id
            ):
                res = (
                    self.repair_id.picking_type_id.default_recycle_location_src_id,
                    res[1],
                )
        return res
