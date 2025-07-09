# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    needs_repair_sync = fields.Boolean(compute="_compute_needs_repair_sync")

    def _get_states_for_sync(self):
        """Return the states in which the repair order can be synchronized."""
        return ["draft", "sent"]

    @api.depends(
        "repair_order_ids.move_ids.repair_create_sync",
        "repair_order_ids.move_ids.repair_update_sync",
    )
    def _compute_needs_repair_sync(self):
        for order in self:
            order.needs_repair_sync = any(
                repair.move_ids.filtered(
                    lambda m: m.repair_create_sync or m.repair_update_sync
                )
                for repair in order.repair_order_ids
            )

    def action_sync_repair_lines(self):
        self.ensure_one()
        if self.state not in self._get_states_for_sync():
            return
        all_moves = self.repair_order_ids.mapped("move_ids")
        all_moves.filtered("repair_create_sync").with_context(
            repair_lines_manual_sync=True
        )._create_repair_sale_order_line()
        all_moves.filtered("repair_update_sync").with_context(
            repair_lines_manual_sync=True
        )._update_repair_sale_order_line()
