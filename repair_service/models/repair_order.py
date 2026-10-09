# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    repair_service_ids = fields.One2many(
        "repair.service", "repair_id", "Services", copy=True
    )

    def action_create_sale_order(self):
        action = super().action_create_sale_order()
        self.repair_service_ids._create_repair_sale_order_line()
        return action
