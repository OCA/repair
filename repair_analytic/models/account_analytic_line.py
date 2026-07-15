# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    repair_order_id = fields.Many2one(
        "repair.order",
        string="Repair Order",
        ondelete="cascade",
        index=True,
    )
