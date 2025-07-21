# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.exceptions import UserError
from odoo.fields import Command


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def _prepare_combined_sale_order_vals(self, partners, picking_types):
        return {
            "company_id": self.company_id.id,
            "partner_id": partners.id,
            "warehouse_id": picking_types.warehouse_id.id,
            "repair_order_ids": [Command.link(ro.id) for ro in self],
        }

    def action_create_combined_sale_order(self):
        if not self:
            return
        already_linked = self.filtered("sale_order_id")
        if already_linked:
            ref_str = "\n".join(ro.name for ro in already_linked)
            error_msg = (
                "You cannot create a quotation for repair orders already linked to "
                f"a sale order:\n{ref_str}"
            )
            raise UserError(self.env._(error_msg))
        picking_types = self.mapped("picking_type_id")
        if not picking_types or len(picking_types) != 1:
            raise UserError(
                self.env._(
                    "All selected repair orders must have the same picking type."
                )
            )

        partners = self.mapped("partner_id")
        if not partners or len(partners) != 1:
            raise UserError(
                self.env._(
                    "All selected repair orders must have the same customer defined."
                )
            )

        sale_order_vals = self._prepare_combined_sale_order_vals(
            partners, picking_types
        )
        self.env["sale.order"].create(sale_order_vals)
        self.mapped("move_ids")._create_repair_sale_order_line()
        return self.action_view_sale_order()
