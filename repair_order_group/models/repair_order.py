# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    """Extend repair.order to support grouping functionality."""

    _inherit = "repair.order"

    group_id = fields.Many2one(
        "repair.order.group",
        string="Order Group",
        ondelete="set null",
        index=True,
        copy=False,
    )
    grouped_repair_ids = fields.One2many(
        related="group_id.repair_ids",
        string="Grouped Repairs",
        readonly=True,
    )

    def action_add_another_repair(self):
        """Create a new repair order in the same group."""
        self.ensure_one()

        if not self.group_id:
            self.group_id = self.env["repair.order.group"].create(
                {
                    "partner_id": self.partner_id.id,
                    "company_id": self.company_id.id,
                }
            )

        new_repair = self.create(
            {
                "group_id": self.group_id.id,
                "partner_id": self.partner_id.id,
                "company_id": self.company_id.id,
                "picking_type_id": self.picking_type_id.id,
                "location_id": self.location_id.id,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "repair.order",
            "res_id": new_repair.id,
            "view_mode": "form",
            "target": "current",
        }

    def write(self, vals):
        """Sync partner changes across group repairs."""
        res = super().write(vals)

        if "partner_id" in vals and not self.env.context.get("skip_group_sync"):
            for repair in self.filtered("group_id"):
                if repair.group_id.partner_id != repair.partner_id:
                    repair.group_id.partner_id = repair.partner_id
                    siblings = repair.group_id.repair_ids - repair
                    if siblings:
                        siblings.with_context(skip_group_sync=True).write(
                            {"partner_id": repair.partner_id.id}
                        )
        return res

    def _action_repair_confirm(self):
        """Cascade confirmation to draft repairs in the same group."""
        res = super()._action_repair_confirm()

        if not self.env.context.get("skip_group_confirm"):
            for repair in self.filtered("group_id"):
                siblings = repair.group_id.repair_ids.filtered(
                    lambda r, rid=repair.id: r.state == "draft" and r.id != rid
                )
                if siblings:
                    siblings.with_context(
                        skip_group_confirm=True
                    )._action_repair_confirm()
        return res

    def action_repair_cancel(self):
        """Cascade cancellation to non-finished repairs in the same group."""
        res = super().action_repair_cancel()

        if not self.env.context.get("skip_group_cancel"):
            for repair in self.filtered("group_id"):
                siblings = repair.group_id.repair_ids.filtered(
                    lambda r, rid=repair.id: (
                        r.state not in ("cancel", "done") and r.id != rid
                    )
                )
                if siblings:
                    siblings.with_context(skip_group_cancel=True).action_repair_cancel()
        return res

    def action_create_sale_order(self):
        """Create quotation for repair or entire group."""
        self.ensure_one()

        if self.sale_order_id:
            raise UserError(
                _(
                    "Repair order %(repair)s is already linked to sale order %(sale)s.",
                    repair=self.name,
                    sale=self.sale_order_id.name,
                )
            )

        if not self.partner_id:
            raise UserError(_("You need to define a customer to create a quotation."))

        if self.group_id:
            return self._create_sale_order_for_group()

        return super().action_create_sale_order()

    def _create_sale_order_for_group(self):
        """Create single sale order for all valid repairs in group."""
        group = self.group_id

        # Repairs that already have sale orders
        existing_repairs = group.repair_ids.filtered(lambda r: r.sale_order_id)
        if existing_repairs:
            raise UserError(
                _(
                    "Some repair orders in this group are already "
                    "linked to sale order %(sale)s.",
                    sale=existing_repairs[0].sale_order_id.name,
                )
            )

        repairs = group.repair_ids.filtered(
            lambda r: not r.sale_order_id and r.state != "cancel"
        )
        if not repairs:
            raise UserError(
                _("No valid repair orders found in the group to create quotation.")
            )

        # Validate consistency across repairs
        if len(repairs.mapped("partner_id")) > 1:
            raise UserError(_("All repairs in the group must have the same customer."))
        if len(repairs.mapped("company_id")) > 1:
            raise UserError(
                _("All repairs in the group must belong to the same company.")
            )
        if len(repairs.mapped("picking_type_id.warehouse_id")) > 1:
            raise UserError(_("All repairs in the group must use the same warehouse."))

        # Use values from the first repair (all should be consistent now)
        first_repair = repairs[0]
        sale_vals = {
            "partner_id": first_repair.partner_id.id,
            "company_id": first_repair.company_id.id,
        }
        if first_repair.picking_type_id and first_repair.picking_type_id.warehouse_id:
            sale_vals["warehouse_id"] = first_repair.picking_type_id.warehouse_id.id

        sale_order = self.env["sale.order"].create(sale_vals)

        # Link all repairs to the sale order
        repairs.sale_order_id = sale_order

        # Create sale order lines
        for repair in repairs:
            repair._create_repair_sale_order_line(sale_order)

        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": sale_order.id,
            "view_mode": "form",
            "target": "current",
        }

    def _create_repair_sale_order_line(self, sale_order):
        """Create sale order line for this repair.

        Price: 0 for warranty, otherwise use order/partner pricelist.
        """
        self.ensure_one()
        if not self.product_id:
            return

        qty = self.product_qty or 1.0
        uom = self.product_uom or self.product_id.uom_id

        if self.under_warranty:
            price_unit = 0.0
        else:
            pricelist = (
                sale_order.pricelist_id or self.partner_id.property_product_pricelist
            )
            if pricelist:
                price_unit = pricelist._get_product_price(
                    self.product_id, qty, partner=self.partner_id, uom_id=uom.id
                )
            else:
                price_unit = self.product_id.list_price

        self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product_id.id,
                "product_uom_qty": qty,
                "product_uom": uom.id,
                "price_unit": price_unit,
                "name": _("Repair: %(name)s", name=self.name),
            }
        )
