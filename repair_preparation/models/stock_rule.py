# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):

    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        move_fields = super()._get_custom_move_fields()
        move_fields += ["repair_line_id"]
        return move_fields
