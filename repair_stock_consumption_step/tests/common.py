# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class Common(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Product to repair", "type": "product"}
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "product to consume", "type": "product"}
        )

        cls.warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "WH",
                "code": "wh_test",
                "repair_consumption_step": True,
            }
        )
        cls.repair_loc = cls.warehouse.lot_stock_id
        cls.production_location = cls.env["stock.location"].search(
            [("usage", "=", "production")], limit=1
        )
        cls.consumption_type = cls.env["stock.picking.type"].create(
            {
                "name": "Consumption",
                "warehouse_id": cls.warehouse.id,
                "code": "internal",
                "sequence_code": "PREP",
                "default_location_src_id": cls.repair_loc.id,
                "default_location_dest_id": cls.production_location.id,
            }
        )
        cls.warehouse.repair_consumption_picking_type_id = cls.consumption_type

        cls.repair = cls.env["repair.order"].create(
            {
                "partner_id": cls.partner.id,
                "product_id": cls.product.id,
                "location_id": cls.repair_loc.id,
                "operations": [
                    Command.create(
                        {
                            "name": "replace product",
                            "type": "add",
                            "price_unit": 100,
                            "product_id": cls.product_c.id,
                            "product_uom_qty": 2.0,
                            "location_id": cls.repair_loc.id,
                            "lot_id": cls.env["stock.lot"]
                            .create(
                                {"name": "Test Lot", "product_id": cls.product_c.id}
                            )
                            .id,
                        }
                    )
                ],
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.repair_loc, 1.0
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_c, cls.repair_loc, 10.0
        )

    @classmethod
    def _do_picking(cls, picking):
        for move in picking.move_ids:
            move.quantity_done = move.product_qty
        picking._action_done()
