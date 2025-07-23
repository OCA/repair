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

    def test_sale_order_lines_grouped_by_section(self):
        sale_order_action = (
            self.env["repair.order"]
            .browse([self.repair_1.id, self.repair_2.id])
            .action_create_combined_sale_order()
        )
        sale_order = self.SaleOrder.browse(sale_order_action["res_id"])
        ordered_lines = sale_order.order_line.sorted(key=lambda line: line.sequence)

        for repair in [self.repair_1, self.repair_2]:
            section_lines = [
                line
                for line in ordered_lines
                if line.display_type == "line_section"
                and line.repair_order_id == repair
            ]
            self.assertEqual(
                len(section_lines),
                1,
                (
                    f"Expected one section line for {repair.name}, "
                    f"found {len(section_lines)}"
                ),
            )
            section_line = section_lines[0]
            product_lines = [
                line
                for line in ordered_lines
                if line.repair_order_id == repair and not line.display_type
            ]
            # All product lines must have sequence greater than section line
            for prod_line in product_lines:
                self.assertGreater(
                    prod_line.sequence,
                    section_line.sequence,
                    (
                        f"Product line for {repair.name} does not follow its "
                        "section line"
                    ),
                )
