# Copyright (C) 2021 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import TransactionCase


class TestRepairType(TransactionCase):
    def test_get_repair_locations_remove(self):
        self.env.ref(
            "repair.picking_type_warehouse0_repair"
        ).default_remove_location_src_id = self.env.ref(
            "stock.stock_location_customers"
        )
        repair = self.env["repair.order"].create(
            {
                "picking_type_id": self.env.ref(
                    "repair.picking_type_warehouse0_repair"
                ).id,
                "product_id": self.env.ref("product.product_product_4").id,
                "product_uom": self.env.ref("uom.product_uom_unit").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Remove Component 1",
                            "repair_line_type": "remove",
                            "product_id": self.env.ref("product.product_product_3").id,
                            "product_uom_qty": 3,
                        },
                    )
                ],
            }
        )
        repair._action_repair_confirm()
        self.assertEqual(
            repair.move_ids.move_line_ids.location_id,
            self.env.ref("stock.stock_location_customers"),
        )

    def test_get_repair_locations_recycle(self):
        self.env.ref(
            "repair.picking_type_warehouse0_repair"
        ).default_recycle_location_src_id = self.env.ref(
            "stock.stock_location_customers"
        )
        repair = self.env["repair.order"].create(
            {
                "picking_type_id": self.env.ref(
                    "repair.picking_type_warehouse0_repair"
                ).id,
                "product_id": self.env.ref("product.product_product_4").id,
                "product_uom": self.env.ref("uom.product_uom_unit").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Recycle Component",
                            "repair_line_type": "recycle",
                            "product_uom_qty": 3,
                            "product_id": self.env.ref("product.product_product_11").id,
                        },
                    )
                ],
            }
        )
        repair._action_repair_confirm()
        self.assertEqual(
            repair.move_ids.move_line_ids.location_id,
            self.env.ref("stock.stock_location_customers"),
        )
