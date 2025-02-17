# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    to_refurbish = fields.Boolean()
    refurbish_location_dest_id = fields.Many2one(
        string="Refurbished Delivery Location", comodel_name="stock.location"
    )
    refurbish_product_id = fields.Many2one(
        string="Refurbished product", comodel_name="product.product"
    )
    refurbish_tracking = fields.Selection(
        string="Refurbished Product Tracking",
        related="refurbish_product_id.tracking",
        readonly=False,
    )
    refurbish_lot_id = fields.Many2one(
        string="Refurbished Lot", comodel_name="stock.lot"
    )
    refurbish_move_id = fields.Many2one(
        string="Refurbished Inventory Move", comodel_name="stock.move"
    )

    @api.onchange("to_refurbish", "product_id")
    def _onchange_to_refurbish(self):
        if self.to_refurbish:
            self.refurbish_product_id = self.product_id.refurbish_product_id
            self.refurbish_location_dest_id = self.location_id
        else:
            self.refurbish_product_id = False
            self.refurbish_location_dest_id = False

    def _get_virtual_refurbish_location(self):
        self.ensure_one()
        return self.product_id.property_stock_refurbish or self.location_dest_id

    def _get_refurbish_stock_move_dict(self):
        refurbish_loc = self._get_virtual_refurbish_location()
        return {
            "name": self.name,
            "product_id": self.refurbish_product_id.id,
            "product_uom": self.product_uom.id or self.refurbish_product_id.uom_id.id,
            "product_uom_qty": self.product_qty,
            "partner_id": self.partner_id and self.partner_id.id or False,
            "location_id": refurbish_loc.id,
            "repair_id": self.id,
            "location_dest_id": self.refurbish_location_dest_id.id,
            "move_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.refurbish_product_id.id,
                        "lot_id": self.refurbish_lot_id.id,
                        "quantity_product_uom": self.product_qty,
                        "product_uom_id": self.product_uom.id
                        or self.refurbish_product_id.uom_id.id,
                        "quantity": self.product_qty,
                        "package_id": False,
                        "result_package_id": False,
                        "location_id": refurbish_loc.id,
                        "location_dest_id": self.refurbish_location_dest_id.id,
                    },
                )
            ],
        }

    def action_repair_done(self):
        to_refurbish_orders = self.filtered("to_refurbish")
        res = super(RepairOrder, (self - to_refurbish_orders)).action_repair_done()
        for repair in to_refurbish_orders:
            refurbish_loc = self._get_virtual_refurbish_location()
            super(
                RepairOrder,
                repair.with_context(
                    force_refurbish_location_dest_id=refurbish_loc.id,
                    to_refurbish=repair.to_refurbish,
                ),
            ).action_repair_done()
            if repair.to_refurbish:
                move = self.env["stock.move"].create(
                    repair._get_refurbish_stock_move_dict()
                )
                move._action_confirm()
                move.quantity = repair.product_qty
                move.picked = True
                move._action_done()
                repair.refurbish_move_id = move.id
        return res
