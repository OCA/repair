# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    consumption_repair_order_id = fields.One2many(
        "repair.order", "consumption_picking_id"
    )

    def _action_done(self):
        res = super()._action_done()
        done_pickings = self.filtered(lambda p: p.state == "done")
        repair_orders = self.env["repair.order"].search(
            [
                ("state", "=", "consumption"),
                ("consumption_picking_id", "in", done_pickings.ids),
            ]
        )
        repair_orders._action_consumption_done()
        return res

    def _check_no_partial_qties_on_repaired_product(self):
        """
        Ensure the consumption pickings can not partially process the qties
        for the repaired product. (Partial quantities are only allowed on
        the spare parts).
        """
        invalid_picks = self.env["stock.picking"]
        for pick in self:
            repair = pick.consumption_repair_order_id
            if not repair:
                continue

            repaired_product_moves = pick.move_ids.filtered(
                lambda m: m.product_id == repair.product_id
            )
            if sum(repaired_product_moves.mapped("product_uom_qty")) != sum(
                repaired_product_moves.mapped("quantity_done")
            ):
                invalid_picks |= pick

        if invalid_picks:
            raise ValidationError(
                _(
                    "Invalid partial quantities on repaired product."
                    "You can only partially process spare parts.\n"
                    "\n"
                    "Picking(s):\n- %s",
                    "\n- ".join(invalid_picks.mapped("name")),
                )
            )

    def _pre_action_done_hook(self):
        partially_processed_pickings = self._check_backorder()
        if partial_consumption_picks := partially_processed_pickings.filtered(
            "consumption_repair_order_id"
        ):
            partial_consumption_picks._check_no_partial_qties_on_repaired_product()
            return partial_consumption_picks._action_repair_consumption_partial_wizard(
                default_pick_ids=partial_consumption_picks.ids
            )
        return super()._pre_action_done_hook()

    def _action_repair_consumption_partial_wizard(self, default_pick_ids):
        view = self.env.ref(
            "repair_stock_consumption_step.repair_consumption_backorder_wizard_form_view"
        )
        return {
            "name": _("Process Unused Spare Parts?"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "repair.consumption.partial.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "context": dict(
                self.env.context,
                default_pick_ids=[(4, _id) for _id in default_pick_ids],
            ),
        }
