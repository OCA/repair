# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import Form, TransactionCase


class TestMrpMtoWithStock(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestMrpMtoWithStock, self).setUp(*args, **kwargs)
        self.repair_obj = self.env["repair.order"]
        self.repair_line_obj = self.env["repair.line"]
        self.product_obj = self.env["product.product"]
        self.move_obj = self.env["stock.move"]
        self.move_line_obj = self.env["stock.move.line"]
        self.stock_production_lot_obj = self.env["stock.production.lot"]

        self.stock_location_stock = self.env.ref("stock.stock_location_stock")
        self.customer_location = self.env.ref("stock.stock_location_customers")
        self.refurbish_loc = self.env.ref("repair_refurbish.stock_location_refurbish")
        self.company = self.env.ref("base.main_company")

        self.refurbish_product = self.product_obj.create(
            {"name": "Refurbished Awesome Screen", "type": "product"}
        )
        self.product = self.product_obj.create(
            {
                "name": "Awesome Screen",
                "type": "product",
                "refurbish_product_id": self.refurbish_product.id,
            }
        )
        self.material = self.product_obj.create({"name": "Materials", "type": "consu"})
        self.material2 = self.product_obj.create(
            {"name": "Materials", "type": "product"}
        )
        self._update_product_qty(self.product, self.stock_location_stock, 10.0)

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
        """Tests that the refusrbih move is created when
        the repair is marked as to refurbish AFTER
        being validated"""
        repair = self.repair_obj.create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "location_dest_id": self.customer_location.id,
                "location_id": self.stock_location_stock.id,
            }
        )
        repair.onchange_product_id()
        # Complete repair:
        repair.action_validate()
        repair.action_repair_start()
        # Make it "to refurbish" in the middle
        repair.refurbish_product_id = self.refurbish_product
        repair.refurbish_location_dest_id = repair.location_dest_id
        repair.location_dest_id = repair.product_id.property_stock_refurbish
        repair.to_refurbish = True
        repair.action_repair_end()
        moves = self.move_obj.search(
            [("reference", "=", repair.name), ("state", "!=", "cancel")]
        )
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
                # check the refurbish moves are created anyway
                self.assertEqual(m.location_id, self.refurbish_loc)
                self.assertEqual(m.location_dest_id, self.customer_location)
                self.assertEqual(
                    m.mapped("move_line_ids.location_id"), self.refurbish_loc
                )
                self.assertEqual(
                    m.mapped("move_line_ids.location_dest_id"), self.customer_location
                )
            else:
                self.assertTrue(
                    False, "Unexpected product: %s" % m.product_id.display_name
                )

    def test_02_lot_selection_existing_lot(self):
        existing_lot_refurbish = self.stock_production_lot_obj.create(
            {
                "product_id": self.refurbish_product.id,
                "name": "Lot B",
                "company_id": self.company.id,
            }
        )
        repair = self.repair_obj.create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "location_dest_id": self.customer_location.id,
                "location_id": self.stock_location_stock.id,
            }
        )
        # Complete repair:
        repair.action_validate()
        repair.action_repair_start()
        # Make it "to refurbish" in the middle
        repair_form = Form(repair)
        repair.refurbish_product_id = self.refurbish_product
        repair.refurbish_location_dest_id = repair.location_dest_id
        repair.location_dest_id = repair.product_id.property_stock_refurbish
        repair.to_refurbish = True
        repair = repair_form.save()
        # assign the lot after saving
        repair_form = Form(repair)
        repair.refurbish_lot_id = existing_lot_refurbish
        repair = repair_form.save()
        repair.action_repair_end()
        moves = self.move_line_obj.search(
            [
                ("move_id.reference", "=", repair.name),
                ("state", "!=", "cancel"),
                ("product_id", "=", self.refurbish_product.id),
            ]
        )
        self.assertEqual(moves.lot_id, existing_lot_refurbish)
