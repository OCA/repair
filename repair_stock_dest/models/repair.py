# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare


class RepairOrder(models.Model):
    _inherit = "repair.order"

    product_location_dest_id = fields.Many2one(
        "stock.location",
        "Product Destination Location",
        compute="_compute_product_location_dest_id",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
        index=True,
        check_company=True,
        help="This is the location where the repaired product will be stored.",
    )

    @api.depends("picking_type_id")
    def _compute_product_location_dest_id(self):
        for repair in self:
            repair.product_location_dest_id = (
                repair.picking_type_id.default_product_location_dest_id
            )

    def action_repair_done(self):
        res = super().action_repair_done()

        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        for repair in self:
            # Ensure the product has been repaired and stock move is done
            if repair.product_location_dest_id and repair.move_id.state == "done":
                owner_id = False
                available_qty_owner = self.env["stock.quant"]._get_available_quantity(
                    repair.product_id,
                    repair.location_id,
                    repair.lot_id,
                    owner_id=repair.partner_id,
                    strict=True,
                )
                if (
                    float_compare(
                        available_qty_owner,
                        repair.product_qty,
                        precision_digits=precision,
                    )
                    >= 0
                ):
                    owner_id = repair.partner_id.id

                transfer_move_vals = {
                    "name": f"Transfer After Repair - {repair.name}",
                    "product_id": repair.product_id.id,
                    "product_uom": repair.product_uom.id or repair.product_id.uom_id.id,
                    "product_uom_qty": repair.product_qty,
                    "partner_id": repair.partner_id.id,
                    "location_id": repair.location_id.id,
                    "location_dest_id": repair.product_location_dest_id.id,
                    "picked": True,
                    "move_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": repair.product_id.id,
                                "lot_id": repair.lot_id.id,
                                "product_uom_id": repair.product_uom.id
                                or repair.product_id.uom_id.id,
                                "quantity": repair.product_qty,
                                "package_id": False,
                                "result_package_id": False,
                                "owner_id": owner_id,
                                "location_id": repair.location_id.id,
                                "company_id": repair.company_id.id,
                                "location_dest_id": repair.product_location_dest_id.id,
                                "consume_line_ids": [
                                    (6, 0, repair.move_ids.move_line_ids.ids)
                                ],
                            },
                        )
                    ],
                    "repair_id": repair.id,
                    "origin": repair.name,
                    "company_id": repair.company_id.id,
                }

                # Create new stock move to transfer the repaired product
                transfer_move = self.env["stock.move"].create(transfer_move_vals)
                transfer_move._action_done(cancel_backorder=True)

        return res
