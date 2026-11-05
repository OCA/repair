# Copyright 2015 Nicola Malcontenti - Agile Business Group
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    discount = fields.Float(
        string="Discount (%)",
        digits="Discount",
    )

    def _prepare_repair_so_line_vals(self):
        vals = super()._prepare_repair_so_line_vals()
        if self.discount and not self.repair_id.under_warranty:
            vals["discount"] = self.discount
        return vals

    def write(self, vals):
        res = super().write(vals)
        if "discount" in vals:
            self._update_repair_sale_order_line_discount()
        return res

    def _update_repair_sale_order_line(self):
        res = super()._update_repair_sale_order_line()
        # The quantity update on the sale line retriggers _compute_discount,
        # which resets the discount from the pricelist rules.
        self.filtered("discount")._update_repair_sale_order_line_discount()
        return res

    def _update_repair_sale_order_line_discount(self):
        for move in self:
            if (
                move.repair_id
                and not move.repair_id.under_warranty
                and move.sale_line_id
                and move.repair_line_type == "add"
            ):
                move.sale_line_id.discount = move.discount
