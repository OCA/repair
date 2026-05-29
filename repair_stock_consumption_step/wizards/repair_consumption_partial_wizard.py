# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, fields, models
from odoo.exceptions import ValidationError


class RepairConsumptionPartialWizard(models.TransientModel):
    _name = "repair.consumption.partial.wizard"
    _description = "Repair Consumption Partial Wizard"

    name = fields.Char()
    pick_ids = fields.Many2many("stock.picking")

    def _get_return_action(self, return_pickings):
        if not return_pickings:
            return {"type": "ir.actions.act_window_close"}

        action = {
            "name": _("Return Consumption Pickings"),
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
        }
        if len(return_pickings) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": return_pickings.id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", return_pickings.ids)],
                }
            )
        return action

    def action_store_back_spare_parts(self):
        self.ensure_one()
        return_pickings = self.env["stock.picking"]
        for picking in self.pick_ids:
            repair = picking.consumption_repair_order_id
            picking.with_context(cancel_backorder=True)._action_done()

            moves_to_return = picking.move_ids.filtered(lambda m: m.state == "cancel")
            if not moves_to_return:
                continue

            return_picking_type = picking.picking_type_id.return_picking_type_id
            if not return_picking_type:
                raise ValidationError(
                    _(
                        "There is no return type configured for the consumption picking "
                        "type: '%(consumption_type)s'. You need to configure one to be able to "
                        "partially process consumption pickings.",
                        consumption_type=picking.picking_type_id.display_name,
                    )
                )

            return_picking = self.env["stock.picking"].create(
                {
                    "partner_id": picking.partner_id.id,
                    "picking_type_id": return_picking_type.id,
                    "location_id": repair.location_id.id,
                    "origin": _("Return of %s", picking.name),
                    "move_ids": [
                        Command.create(
                            {
                                "name": _("Return of %s", move.display_name),
                                "product_id": move.product_id.id,
                                "product_uom_qty": move.product_uom_qty,
                                "product_uom": move.product_uom.id,
                                "location_id": repair.location_id.id,
                                "location_dest_id": (
                                    return_picking_type.default_location_dest_id.id
                                ),
                                "origin_returned_move_id": move.id,
                            },
                        )
                        for move in moves_to_return
                    ],
                }
            )
            return_picking.action_confirm()
            return_picking.action_assign()
            return_pickings |= return_picking

            odoobot = self.env.ref("base.partner_root")
            repair.message_post(
                body=_(
                    "The consumption picking '%(consumption_picking)s' has been partially "
                    "processed. A return picking '%(return_picking)s' has been created to "
                    "store back unconsumed products.",
                    consumption_picking=picking.name,
                    return_picking=return_picking.name,
                ),
                author_id=odoobot.id,
            )

            return_consumption_moves = return_picking.move_ids
            repair._update_parts(return_consumption_moves)

        return self._get_return_action(return_pickings)
