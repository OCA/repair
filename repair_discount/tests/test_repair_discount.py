# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestRepairDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create({"name": "Test customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "is_storable": True,
                "list_price": 20,
            }
        )
        cls.part = cls.env["product.product"].create(
            {
                "name": "Test part",
                "is_storable": True,
                "list_price": 20,
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.repair = cls.env["repair.order"].create(
            {
                "product_id": cls.product.id,
                "partner_id": cls.partner.id,
                "picking_type_id": cls.warehouse.repair_type_id.id,
                "move_ids": [
                    Command.create(
                        {
                            "repair_line_type": "add",
                            "product_id": cls.part.id,
                            "product_uom_qty": 1,
                            "discount": 50,
                        }
                    )
                ],
            }
        )

    def test_discount_on_quotation(self):
        self.repair.action_create_sale_order()
        line = self.repair.move_ids.sale_line_id
        self.assertEqual(line.discount, 50)
        self.assertAlmostEqual(line.price_subtotal, 10)

    def test_discount_updated_after_quotation(self):
        self.repair.action_create_sale_order()
        move = self.repair.move_ids
        move.discount = 10
        self.assertEqual(move.sale_line_id.discount, 10)
        move.discount = 0
        self.assertEqual(move.sale_line_id.discount, 0)

    def test_part_added_after_quotation(self):
        self.repair.action_create_sale_order()
        part2 = self.env["product.product"].create(
            {
                "name": "Test part 2",
                "is_storable": True,
                "list_price": 40,
            }
        )
        self.repair.write(
            {
                "move_ids": [
                    Command.create(
                        {
                            "repair_line_type": "add",
                            "product_id": part2.id,
                            "product_uom_qty": 1,
                            "discount": 25,
                        }
                    )
                ]
            }
        )
        move = self.repair.move_ids.filtered(lambda m: m.product_id == part2)
        self.assertEqual(move.sale_line_id.discount, 25)
        self.assertAlmostEqual(move.sale_line_id.price_subtotal, 30)

    def test_discount_kept_on_quantity_update(self):
        self.repair.action_create_sale_order()
        move = self.repair.move_ids
        move.product_uom_qty = 2
        self.assertEqual(move.sale_line_id.product_uom_qty, 2)
        self.assertEqual(move.sale_line_id.discount, 50)

    def test_no_discount_under_warranty(self):
        self.repair.under_warranty = True
        self.repair.action_create_sale_order()
        line = self.repair.move_ids.sale_line_id
        self.assertEqual(line.discount, 0)
        self.assertEqual(line.price_unit, 0)
