# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestMrpMtoWithStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repair_obj = cls.env["repair.order"]
        cls.product_obj = cls.env["product.product"]
        cls.move_obj = cls.env["stock.move"]

        cls.stock_location_stock = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.refurbish_loc = cls.env.ref("repair_refurbish.stock_location_refurbish")

        cls.refurbish_product = cls.product_obj.create(
            {"name": "Refurbished Awesome Screen", "type": "product"}
        )
        cls.product = cls.product_obj.create(
            {
                "name": "Awesome Screen",
                "type": "product",
                "refurbish_product_id": cls.refurbish_product.id,
            }
        )
        cls.material = cls.product_obj.create({"name": "Materials", "type": "consu"})
        cls.material2 = cls.product_obj.create({"name": "Materials", "type": "product"})
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

    def test_01_repair_refurbish(self):
        """Tests that locations are properly set with a product to
        refurbish, then complete repair."""
        repair = self.repair_obj.create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "location_dest_id": self.customer_location.id,
                "location_id": self.stock_location_stock.id,
            }
        )
        self.assertFalse(repair.to_refurbish)
        repair.to_refurbish = True
        repair._onchange_to_refurbish()
        self.assertEqual(repair.refurbish_location_dest_id, self.customer_location)
        self.assertEqual(repair.location_dest_id, self.product.property_stock_refurbish)

        # Complete repair:
        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()
        moves = self.move_obj.search([("reference", "=", repair.name)])
        self.assertEqual(len(moves), 2)
        for m in moves:
            self.assertEqual(m.state, "done")
            if m.product_id == self.product:
                self.assertEqual(m.location_id, self.stock_location_stock)
                self.assertEqual(m.location_dest_id, self.refurbish_loc)
                self.assertEqual(
                    m.mapped("move_line_ids.location_id"), self.stock_location_stock
                )
                self.assertEqual(
                    m.mapped("move_line_ids.location_dest_id"), self.refurbish_loc
                )
            elif m.product_id == self.refurbish_product:
                self.assertEqual(m.location_id, self.refurbish_loc)
                self.assertEqual(m.location_dest_id, self.customer_location)
                self.assertEqual(
                    m.mapped("move_line_ids.location_id"), self.refurbish_loc
                )
                self.assertEqual(
                    m.mapped("move_line_ids.location_dest_id"), self.customer_location
                )
            else:
                self.assertTrue(False, "Unexpected move.")

    def test_02_repair_no_refurbish(self):
        """Tests normal repairs does not fail and normal location for consumed
        material"""
        repair = self.repair_obj.create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "location_dest_id": self.customer_location.id,
                "to_refurbish": False,
                "location_id": self.stock_location_stock.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.material2.id,
                            "product_uom_qty": 1.0,
                            "state": "draft",
                            "repair_line_type": "add",
                            "location_id": self.stock_location_stock.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )

        # Complete repair:
        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()
        move = self.move_obj.search(
            [("product_id", "=", self.material2.id)], order="create_date desc", limit=1
        )[0]
        self.assertEqual(move.location_dest_id, self.customer_location)
