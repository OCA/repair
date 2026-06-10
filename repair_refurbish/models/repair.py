# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command, api, fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    to_refurbish = fields.Boolean(
        readonly=True, states={"draft": [("readonly", False)]}
    )
    refurbish_product_id = fields.Many2one(
        string="Refurbished product",
        comodel_name="product.product",
        compute="_compute_refurbish_product_id",
        store=True,
        readonly=False,
    )
    refurbish_lot_id = fields.Many2one(
        string="Refurbished Lot", comodel_name="stock.lot"
    )
    refurbish_move_id = fields.Many2one(
        string="Refurbished Inventory Move", comodel_name="stock.move", readonly=True
    )

    @api.depends("to_refurbish", "product_id")
    def _compute_refurbish_product_id(self):
        for repair in self:
            if repair.to_refurbish and repair.product_id:
                repair.refurbish_product_id = repair.product_id.refurbish_product_id
            else:
                repair.refurbish_product_id = False

    def _get_refurbish_move_vals(self):
        refurbish_loc = self.env.ref("repair_refurbish.stock_location_refurbish")
        return {
            "name": self.name,
            "product_id": self.refurbish_product_id.id,
            "product_uom": self.product_uom.id or self.product_id.uom_id.id,
            "product_uom_qty": self.product_qty,
            "partner_id": self.address_id.id,
            "location_id": refurbish_loc.id,
            "location_dest_id": self.location_id.id,
            "move_line_ids": [
                Command.create(
                    {
                        "product_id": self.product_id.id,
                        "lot_id": self.lot_id.id,
                        "reserved_uom_qty": 0,  # bypass reservation here
                        "product_uom_id": self.product_uom.id
                        or self.product_id.uom_id.id,
                        "qty_done": self.product_qty,
                        "package_id": False,
                        "result_package_id": False,
                        "location_id": self.location_id.id,
                        "company_id": self.company_id.id,
                        "location_dest_id": self.location_id.id,
                    },
                )
            ],
            "repair_id": self.id,
            "origin": self.name,
            "company_id": self.company_id.id,
        }

    def action_repair_done(self):
        # We need to use context because the origin odoo core function
        # does not provide a hook
        res = super(
            RepairOrder,
            self.with_context(
                to_refurbish=self.to_refurbish,
            ),
        ).action_repair_done()

        for repair in self:
            if repair.to_refurbish:
                repair.refurbish_move_id = self.env["stock.move"].create(
                    self._get_refurbish_move_vals()
                )
                repair.refurbish_move_id._action_done()
        return res
