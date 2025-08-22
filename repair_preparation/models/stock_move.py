# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):

    _inherit = "stock.move"

    repair_line_id = fields.Many2one(
        comodel_name="repair.line", ondelete="cascade", readonly=True
    )

    def _prepare_procurement_values(self):
        res = super()._prepare_procurement_values()
        if self.repair_line_id:
            res["repair_line_id"] = self.repair_line_id.id
        return res
