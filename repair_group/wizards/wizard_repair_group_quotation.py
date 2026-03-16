# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import _, fields, models
from odoo.exceptions import UserError


class RepairGroupQuotationWizard(models.TransientModel):
    _name = "repair.group.quotation.wizard"
    _description = "Wizard to select quotations to merge"

    repair_group_id = fields.Many2one(
        "repair.group",
        string="Repair Group",
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        "repair.group.quotation.wizard.line",
        "wizard_id",
        string="Quotations",
    )

    def action_create_complete_sale_order(self):
        self.ensure_one()
        selected_lines = self.line_ids.filtered("selected")
        if not selected_lines:
            raise UserError(_("Please select at least one quotation to merge."))

        SaleOrder = self.env["sale.order"]
        SaleOrderLine = self.env["sale.order.line"]
        group = self.repair_group_id

        first_order = selected_lines[0].sale_order_id
        complete_order_vals = {
            "partner_id": group.partner_id.id,
            "user_id": group.user_id.id,
            "company_id": group.company_id.id,
            "date_order": fields.Datetime.now(),
            "note": _("Combined order from Repair Group: {}").format(group.name),
        }

        if first_order.payment_term_id:
            complete_order_vals["payment_term_id"] = first_order.payment_term_id.id
        if first_order.pricelist_id:
            complete_order_vals["pricelist_id"] = first_order.pricelist_id.id

        complete_order = SaleOrder.create(complete_order_vals)

        for line in selected_lines:
            for order_line in line.sale_order_id.order_line:
                line_vals = {
                    "order_id": complete_order.id,
                    "product_id": order_line.product_id.id,
                    "name": order_line.name,
                    "product_uom_qty": order_line.product_uom_qty,
                    "product_uom": order_line.product_uom.id,
                    "price_unit": order_line.price_unit,
                    "tax_id": [(6, 0, order_line.tax_id.ids)],
                    "discount": order_line.discount,
                }
                if (
                    hasattr(order_line, "analytic_distribution")
                    and order_line.analytic_distribution
                ):
                    line_vals["analytic_distribution"] = (
                        order_line.analytic_distribution
                    )
                SaleOrderLine.create(line_vals)

        group.complete_sale_order_id = complete_order
        return {"type": "ir.actions.act_window_close"}


class RepairGroupQuotationWizardLine(models.TransientModel):
    _name = "repair.group.quotation.wizard.line"
    _description = "Wizard line for quotation selection"

    wizard_id = fields.Many2one(
        "repair.group.quotation.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    sale_order_id = fields.Many2one("sale.order", string="Quotation", readonly=True)
    repair_order_id = fields.Many2one(
        "repair.order", string="Repair Order", readonly=True
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        related="repair_order_id.product_id",
        readonly=True,
    )
    amount_total = fields.Monetary(
        string="Total",
        related="sale_order_id.amount_total",
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="sale_order_id.currency_id",
        readonly=True,
    )
    selected = fields.Boolean(string="Include", default=True)
