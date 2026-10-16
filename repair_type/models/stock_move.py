# Copyright (C) 2024 APSL-Nagarro Antoni Marroig
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


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

    def _compute_location_id(self):
        ids_to_super = set()
        for move in self:
            if move.repair_line_type and move.repair_id:
                location_src, _ = move._get_repair_locations(move.repair_line_type)
                move.location_id = location_src
            else:
                ids_to_super.add(move.id)
        return super(StockMove, self.browse(ids_to_super))._compute_location_id()

    @api.depends("repair_id.location_dest_id", "repair_line_type")
    def _compute_location_dest_id(self):
        ids_to_super = set()
        for move in self:
            if move.repair_id and move.repair_line_type:
                _, location_dest = move._get_repair_locations(move.repair_line_type)
                move.location_dest_id = location_dest
            else:
                ids_to_super.add(move.id)
        return super(StockMove, self.browse(ids_to_super))._compute_location_dest_id()
