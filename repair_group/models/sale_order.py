# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    repair_group_id = fields.Many2one(
        "repair.group",
        string="Repair Group",
        compute="_compute_repair_group_id",
        store=False,
    )
    main_repair_sale_id = fields.Many2one(
        "sale.order",
        string="Main Repair Sale Order",
        compute="_compute_repair_info",
    )
    source_sale_order_ids = fields.Many2many(
        "sale.order",
        string="Source Sale Orders",
        compute="_compute_source_sale_order_ids",
    )
    is_repair_main_order = fields.Boolean(compute="_compute_is_repair_main_order")

    @api.depends()
    def _compute_repair_group_id(self):
        for order in self:
            repair = self.env["repair.order"].search(
                [("sale_order_id", "=", order.id), ("repair_group_id", "!=", False)],
                limit=1,
            )
            if repair:
                order.repair_group_id = repair.repair_group_id
            else:
                group = self.env["repair.group"].search(
                    [("complete_sale_order_id", "=", order.id)], limit=1
                )
                order.repair_group_id = group

    @api.depends("repair_group_id")
    def _compute_is_repair_main_order(self):
        for order in self:
            order.is_repair_main_order = (
                order.repair_group_id
                and order.repair_group_id.complete_sale_order_id == order
            )

    @api.depends("repair_group_id", "is_repair_main_order")
    def _compute_source_sale_order_ids(self):
        for order in self:
            if order.is_repair_main_order:
                order.source_sale_order_ids = order.repair_group_id.sale_order_ids
            else:
                order.source_sale_order_ids = False

    @api.depends("repair_group_id")
    def _compute_repair_info(self):
        for order in self:
            order.main_repair_sale_id = order.repair_group_id.complete_sale_order_id

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            groups = self.env["repair.group"].search(
                [("complete_sale_order_id", "=", order.id)]
            )
            for group in groups:
                for repair_order in group.repair_order_ids:
                    if (
                        repair_order.sale_order_id
                        and repair_order.sale_order_id.state in ["draft", "sent"]
                    ):
                        repair_order.sale_order_id.action_confirm()

                    if repair_order.state == "draft":
                        if hasattr(repair_order, "_action_repair_confirm"):
                            repair_order._action_repair_confirm()
                        elif hasattr(repair_order, "action_validate"):
                            repair_order.action_validate()

                if group.state != "under_repair":
                    group.write({"state": "under_repair"})
        return res

    def _action_cancel(self):
        res = super()._action_cancel()
        for order in self:
            groups = self.env["repair.group"].search(
                [("complete_sale_order_id", "=", order.id)]
            )
            for group in groups:
                for repair_order in group.repair_order_ids:
                    if (
                        repair_order.sale_order_id
                        and repair_order.sale_order_id.state != "cancel"
                    ):
                        repair_order.sale_order_id._action_cancel()
        return res
