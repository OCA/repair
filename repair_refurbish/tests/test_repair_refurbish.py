# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestMrpMtoWithStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.stock_location_stock = cls.env.ref("stock.stock_location_stock")
        cls.refurbish_loc = cls.env.ref("repair_refurbish.stock_location_refurbish")
        cls.refurbish_scrap_loc = cls.env.ref(
            "repair_refurbish.stock_location_refurbish_scrap"
        )

        cls.refurbish_product = cls.env["product.product"].create(
            {"name": "Refurbished Awesome Screen", "type": "product"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Awesome Screen",
                "type": "product",
                "refurbish_product_id": cls.refurbish_product.id,
            }
        )
        cls._update_product_qty(cls, cls.product, cls.stock_location_stock, 10.0)

    def _update_product_qty(self, product, location, quantity):
        self.env["stock.quant"].create(
            {
                "location_id": location.id,
                "product_id": product.id,
                "inventory_quantity": quantity,
            }
        ).action_apply_inventory()
        return quantity

    def test_repair_refurbish(self):
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location_stock.id,
                "to_refurbish": True,
            }
        )

        self.assertEqual(repair.refurbish_product_id, self.refurbish_product)
        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()

        self.assertEqual(repair.move_id.location_id, repair.location_id)
        self.assertEqual(repair.move_id.location_dest_id, self.refurbish_scrap_loc)

        self.assertTrue(repair.refurbish_move_id)
        self.assertEqual(repair.refurbish_move_id.location_id, self.refurbish_loc)
        self.assertEqual(repair.refurbish_move_id.location_dest_id, repair.location_id)

    def test_repair_no_refurbish(self):
        """
        Enure the normal case is not broken
        """
        repair = self.env["repair.order"].create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location_stock.id,
                "to_refurbish": False,
            }
        )
        self.assertFalse(repair.refurbish_product_id)

        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()

        self.assertEqual(repair.move_id.location_id, repair.location_id)
        self.assertEqual(repair.move_id.location_dest_id, repair.location_id)
