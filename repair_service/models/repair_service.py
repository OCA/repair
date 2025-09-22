# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools.misc import groupby


class RepairService(models.Model):
    _name = "repair.service"
    _description = "Repair Service"

    repair_id = fields.Many2one(
        "repair.order", "Repair Order Reference", ondelete="cascade", required=True
    )
    display_name = fields.Text(
        "Description",
        required=True,
        compute="_compute_display_name",
        inverse="_inverse_display_name",
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
    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line", string="Sale Line", copy=False
    )

    @api.depends("product_id")
    def _compute_display_name(self):
        for service in self:
            service.display_name = service.product_id.name

    def _inverse_display_name(self):
        # Do nothing, just avoid the compute to overwrite user values
        return

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
            "name": self.display_name,
        }

        if self.repair_id.under_warranty:
            vals["price_unit"] = 0.0
        elif self.product_id.lst_price:
            vals["price_unit"] = self.product_id.lst_price
        return vals

    def _create_repair_sale_order_line(self):
        if not self:
            return
        for service in self:
            if not service.repair_id.sale_order_id:
                continue
            product_qty = (
                service.product_uom_qty
                if service.repair_id.state != "done"
                else service.product_uom_qty
            )
            vals = service._prepare_sale_order_line_vals(product_qty)
            sale_order_line = self.env["sale.order.line"].sudo().create(vals)
            service.sale_line_id = sale_order_line.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("repair_id") or "repair_line_type" not in vals:
                continue
        services = super().create(vals_list)
        services_to_create_so_line = self.env["repair.service"]
        for service in services:
            if not service.repair_id:
                continue
            if not service.sale_line_id:
                services_to_create_so_line |= service
        services_to_create_so_line._create_repair_sale_order_line()
        return services

    def write(self, vals):
        res = super().write(vals)
        repair_services = self.env["repair.service"]
        services_to_create_so_line = self.env["repair.service"]
        for service in self:
            if not service.repair_id:
                continue
            # checks vals update
            if not service.sale_line_id and "sale_line_id" not in vals:
                services_to_create_so_line |= service
            if service.sale_line_id and "product_uom_qty" in vals:
                repair_services |= service

        repair_services._update_repair_sale_order_line()
        services_to_create_so_line._create_repair_sale_order_line()
        return res

    def _update_repair_sale_order_line(self):
        if not self:
            return
        services_to_update = self.env["repair.service"]
        for service in self:
            if not service.repair_id:
                continue
            if service.sale_line_id:
                services_to_update |= service
        for sale_line, _ in groupby(services_to_update, lambda m: m.sale_line_id):
            sale_line.product_uom_qty = sum(
                sale_line.repair_service_ids.mapped("product_uom_qty")
            )
