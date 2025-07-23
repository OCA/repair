# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_section_group(self):
        """Get the repair to group by from sale order's repair_order_ids"""
        return self.repair_order_id

    def _action_launch_stock_rule(self, **kwargs):
        # The criteria used in repair base module is not working
        # when adding extra lines for sections and services
        # TODO: this may need to be in a glue module bewteen
        #  sale_procurement_group_by_line and repair_service
        # it seems the root cause is the not compatibility
        # between them
        lines_without_repair_move = self.filtered(
            lambda line: not line.repair_order_id and not line.display_type
        )
        return super(
            SaleOrderLine, lines_without_repair_move
        )._action_launch_stock_rule(**kwargs)
