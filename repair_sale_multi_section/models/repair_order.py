# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    def action_create_combined_sale_order(self):
        res = super().action_create_combined_sale_order()
        self.repair_service_ids._create_repair_sale_order_line()
        self.mapped("sale_order_id").action_create_repair_sections()
        return res

    def action_create_sale_order(self):
        # for single repair in quote we add sections as well
        res = super().action_create_sale_order()
        self.mapped("sale_order_id").action_create_repair_sections()
        return res

    def _get_section_grouping(self):
        return "id"

    def _get_section_grouping(self):
        """Return grouping criteria for repairs"""
        return self
