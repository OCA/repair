# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # `repair_id` is reserved to the stock.moves directly related
    # to the execution of the repair order and has associated logic
    # in odoo core code (like assigning the picking type)
    # To avoid unexpected behaviors, we use `related_repair_id` to
    # signal auxiliar stock moves that are not directly related to
    # repair execution.
    related_repair_id = fields.Many2one(
        comodel_name="repair.order",
        readonly=True,
    )
