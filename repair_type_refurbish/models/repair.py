# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class Repair(models.Model):
    _inherit = "repair.order"

    refurbish_location_dest_id = fields.Many2one(
        compute="_compute_refurbish_location_dest_id", store=True, readonly=False
    )

    @api.depends("repair_type_id")
    def _compute_refurbish_location_dest_id(self):
        for rec in self:
            if rec.repair_type_id.refurbish_location_dest_id:
                rec.refurbish_location_dest_id = (
                    rec.repair_type_id.refurbish_location_dest_id
                )
