# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRepairQuoteFromMultiple(TransactionCase):
    def setUp(self):
        super().setUp()
        self.RepairOrder = self.env["repair.order"]
        self.SaleOrder = self.env["sale.order"]
        self.Move = self.env["stock.move"]
        self.Product = self.env["product.product"]
        self.StockPickingType = self.env["stock.picking.type"]

        self.partner = self.env.ref("base.res_partner_1")
        self.uom_unit = self.env.ref("uom.product_uom_unit")

        self.product = self.Product.create(
            {
                "name": "Test Spare Part",
                "type": "consu",
                "is_storable": True,
                "uom_id": self.uom_unit.id,
            }
        )

        self.src_location = self.env.ref("stock.stock_location_stock")
        self.dest_location = self.env.ref("stock.stock_location_customers")
        self.parts_location = self.env.ref("stock.stock_location_stock")
        self.repair_1 = self.RepairOrder.create(
            {
                "name": "Repair A",
                "partner_id": self.partner.id,
                "product_location_src_id": self.src_location.id,
                "product_location_dest_id": self.dest_location.id,
                "parts_location_id": self.parts_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.uom_unit.id,
                            "state": "draft",
                            "repair_line_type": "add",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2.0,
                            "product_uom": self.uom_unit.id,
                            "state": "draft",
                            "repair_line_type": "add",
                        },
                    ),
                ],
            }
        )
        self.repair_2 = self.RepairOrder.create(
            {
                "name": "Repair B",
                "partner_id": self.partner.id,
                "product_location_src_id": self.src_location.id,
                "product_location_dest_id": self.dest_location.id,
                "parts_location_id": self.parts_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 3.0,
                            "product_uom": self.uom_unit.id,
                            "state": "draft",
                            "repair_line_type": "add",
                        },
                    ),
                ],
            }
        )

    def test_create_single_quote_from_multiple_repairs(self):
        sale_order_action = (
            self.env["repair.order"]
            .browse([self.repair_1.id, self.repair_2.id])
            .action_create_combined_sale_order()
        )
        sale_order = self.SaleOrder.browse(sale_order_action["res_id"])
        self.assertEqual(
            sale_order.repair_order_ids.ids, [self.repair_1.id, self.repair_2.id]
        )
        self.assertEqual(self.repair_1.sale_order_id.id, sale_order.id)
        self.assertEqual(self.repair_2.sale_order_id.id, sale_order.id)

        lines = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.product
        )
        self.assertEqual(len(lines), 3)
        self.assertEqual(sum(lines.mapped("product_uom_qty")), 6.0)
