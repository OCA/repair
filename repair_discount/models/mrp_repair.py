# Copyright 2015 Nicola Malcontenti - Agile Business Group
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RepairFee(models.Model):
    _inherit = "repair.fee"

    discount = fields.Float(
        string="Discount (%)",
        store=True,
    )

    @api.depends("discount")
    def _compute_price_total_and_subtotal(self):
        res = super(RepairFee, self)._compute_price_total_and_subtotal()
        for fee in self:
            discount_factor = 1 - fee.discount / 100.0
            fee.price_total *= discount_factor
            fee.price_subtotal *= discount_factor
        return res


class RepairLine(models.Model):
    _inherit = "repair.line"

    discount = fields.Float(
        string="Discount (%)",
        store=True,
    )

    @api.depends("discount")
    def _compute_price_total_and_subtotal(self):
        res = super(RepairLine, self)._compute_price_total_and_subtotal()
        for line in self:
            discount_factor = 1 - line.discount / 100.0
            line.price_total *= discount_factor
            line.price_subtotal *= discount_factor
        return res


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def _create_invoices(self, group=False):
        res = super(RepairOrder, self)._create_invoices(group)
        for repair in self.filtered(lambda _repair: _repair.invoice_method != "none"):
            operations = repair.operations
            fees_lines = repair.fees_lines
            for op in operations.filtered(
                lambda item: item.discount and item.invoice_line_id
            ):
                op.invoice_line_id.with_context(check_move_validity=False).update(
                    {"discount": op.discount}
                )
            for fee_lines in fees_lines.filtered(
                lambda item: item.discount and item.invoice_line_id
            ):
                fee_lines.invoice_line_id.with_context(
                    check_move_validity=False
                ).update({"discount": fee_lines.discount})
        return res

    def _calculate_line_base_price(self, line):
        return line.price_unit * (1 - (line.discount or 0.0) / 100.0)

    @api.depends(
        "operations", "fees_lines", "operations.invoiced", "fees_lines.invoiced"
    )
    def _amount_tax(self):
        res = super(RepairOrder, self)._amount_tax()
        for repair in self:
            taxed_amount = 0.0
            currency = repair.pricelist_id.currency_id
            for line in repair.operations:
                tax_calculate = line.tax_id.compute_all(
                    self._calculate_line_base_price(line),
                    repair.pricelist_id.currency_id,
                    line.product_uom_qty,
                    line.product_id,
                    repair.partner_id,
                )
                for c in tax_calculate["taxes"]:
                    taxed_amount += c["amount"]
            for line in repair.fees_lines:
                tax_calculate = line.tax_id.compute_all(
                    self._calculate_line_base_price(line),
                    repair.pricelist_id.currency_id,
                    line.product_uom_qty,
                    line.product_id,
                    repair.partner_id,
                )
                for c in tax_calculate["taxes"]:
                    taxed_amount += c["amount"]
            repair.amount_tax = currency.round(taxed_amount)
        return res
