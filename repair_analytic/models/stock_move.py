# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Company Currency",
    )
    cost = fields.Float(
        string="Cost",
        related="product_id.standard_price",
        groups="base.group_user",
        help="Product cost, used when the repair operation type's "
        "Analytic Price Type is set to 'Cost'.",
    )

    def _repair_analytic_default_price_unit(self):
        """Default Price from the product's Sales Price on repair 'add'
        lines, without overriding a value already set (manually or by the
        sale_line_id-driven pricing flow).

        Price is read-only in the Parts list, so this cannot rely on the
        client-side onchange alone: a readonly field's onchange-computed
        value does not reliably survive further edits to the same row
        (e.g. typing Quantity) before the row is saved. create()/write()
        are the authoritative, server-side guarantee; the onchange below
        only provides immediate visual feedback while editing.
        """
        for move in self:
            if (
                move.repair_id
                and move.repair_line_type == "add"
                and move.product_id
                and not move.sale_line_id
                and not move.price_unit
            ):
                move.price_unit = move.product_id.list_price

    @api.onchange("product_id")
    def _onchange_product_id_repair_analytic_price_unit(self):
        self._repair_analytic_default_price_unit()

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._repair_analytic_default_price_unit()
        return moves

    def write(self, vals):
        res = super().write(vals)
        if "product_id" in vals or "repair_line_type" in vals:
            self._repair_analytic_default_price_unit()
        return res

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        for move, vals in zip(self, vals_list, strict=False):
            if move.repair_id:
                vals["price_unit"] = move.price_unit
        return vals_list
