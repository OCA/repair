# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RepairService(models.Model):
    _name = "repair.service"

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

    @api.depends("product_id")
    def _compute_name(self):
        for service in self:
            service.display_name = service.product_id.name

    @api.depends("product_id")
    def _compute_product_uom(self):
        for service in self:
            service.product_uom = service.product_id.uom_id

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
            so_line_vals.append(
                {
                    "order_id": service.repair_id.sale_order_id.id,
                    "product_id": service.product_id.id,
                    "product_uom_qty": product_qty,
                }
            )
            if service.repair_id.under_warranty:
                so_line_vals[-1]["price_unit"] = 0.0
            elif service.product_id.lst_price:
                so_line_vals[-1]["price_unit"] = service.product_id.lst_price
        self.env["sale.order.line"].create(so_line_vals)
