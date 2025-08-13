# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RepairService(models.Model):
    _name = "repair.service"
    _description = "Repair Service"

    repair_id = fields.Many2one(
        "repair.order", "Repair Order Reference", ondelete="cascade", required=True
    )
    display_name = fields.Text(
        "Description",
        required=True,
        compute="_compute_name",
        store=True,
        precompute=True,
    )
    product_id = fields.Many2one(
        "product.product", "Product", domain=[("type", "=", "service")], required=True
    )
    product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
    product_uom = fields.Many2one(
        "uom.uom",
        required=True,
        domain="[('category_id', '=', product_uom_category_id)]",
        readonly=False,
        precompute=True,
        compute="_compute_product_uom",
        store=True,
    )
    product_uom_qty = fields.Float(
        "Quantity", digits="Product Unit of Measure", required=True, default=1.0
    )
    company_id = fields.Many2one(related="repair_id.company_id")

    @api.depends("product_id")
    def _compute_name(self):
        for service in self:
            service.display_name = service.product_id.name

    @api.depends("product_id")
    def _compute_product_uom(self):
        for service in self:
            service.product_uom = service.product_id.uom_id

    def _prepare_sale_order_line_vals(self, product_qty):
        self.ensure_one()
        vals = {
            "order_id": self.repair_id.sale_order_id.id,
            "product_id": self.product_id.id,
            "product_uom_qty": product_qty,
            "product_uom": self.product_uom.id,
        }
        if self.repair_id.under_warranty:
            vals["price_unit"] = 0.0
        elif self.product_id.lst_price:
            vals["price_unit"] = self.product_id.lst_price
        return vals

    def _create_repair_sale_order_line(self):
        if not self:
            return
        so_line_vals = []
        for service in self:
            if not service.repair_id.sale_order_id:
                continue
            product_qty = (
                service.product_uom_qty
                if service.repair_id.state != "done"
                else service.product_uom_qty
            )
            vals = service._prepare_sale_order_line_vals(product_qty)
            so_line_vals.append(vals)
        self.env["sale.order.line"].create(so_line_vals)
