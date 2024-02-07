# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_repair_scrap = fields.Boolean(
        string="Is repair Scrap",
        copy=False,
        help="This Stock Move has been created from a Scrap operation in the Repair.",
    )
