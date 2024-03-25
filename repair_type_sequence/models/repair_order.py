# Copyright 2023 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    @api.model
    def create(self, vals):
        rorder = super(RepairOrder, self).create(vals)
        if rorder.repair_type_id:
            sequence_id = (
                self.env["repair.type"].browse(vals["repair_type_id"]).sequence_id
            )
            if sequence_id:
                rorder.name = sequence_id._next()
        return rorder

    def write(self, vals):
        res = False
        for rec in self:
            new_rtype_id = vals.get("repair_type_id", False)
            new_rtype = self.env["repair.type"].browse(new_rtype_id)
            if new_rtype and new_rtype.sequence_id:
                vals["name"] = new_rtype.sequence_id._next()
            res = super(RepairOrder, rec).write(vals)
        return res
