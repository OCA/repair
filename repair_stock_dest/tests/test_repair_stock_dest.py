# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairStockDest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.stock_location = cls.env["stock.location"].create(
            {
                "name": "Stock Location",
                "usage": "internal",
            }
        )

        cls.product_destination_location = cls.env["stock.location"].create(
            {
                "name": "Product Destination Location",
                "usage": "internal",
            }
        )

        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Repair Operation Type",
                "code": "repair_operation",
                "default_location_src_id": cls.stock_location.id,
                "default_product_location_dest_id": cls.product_destination_location.id,
                "sequence_code": "RO",
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

        cls.repair_order = cls.env["repair.order"].create(
            {
                "name": "Test Repair Order",
                "picking_type_id": cls.picking_type.id,
                "product_id": cls.product.id,
            }
        )

        # Create stock move linked to the repair order
        cls.stock_move = cls.env["stock.move"].create(
            {
                "name": "Test Stock Move",
                "product_id": cls.product.id,
                "product_uom_qty": 1,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.stock_location.id,
                "picking_type_id": cls.picking_type.id,
                "repair_id": cls.repair_order.id,
            }
        )
        cls.repair_order.move_id = cls.stock_move

    def test_product_location_dest_id_computation(self):
        """Test that product_location_dest_id is correctly computed."""
        self.repair_order._compute_product_location_dest_id()
        self.assertEqual(
            self.repair_order.product_location_dest_id,
            self.picking_type.default_product_location_dest_id,
            "The product_location_dest_id should be set to the default location.",
        )

    def test_product_location_dest_id_modification(self):
        """Test that product_location_dest_id can be manually modified."""
        custom_location = self.env["stock.location"].create(
            {"name": "Custom Location", "usage": "internal"}
        )

        self.repair_order.product_location_dest_id = custom_location.id
        self.assertEqual(
            self.repair_order.product_location_dest_id,
            custom_location,
            "The product_location_dest_id should be modifiable by the user.",
        )

    def test_action_repair_done_creates_new_move(self):
        """Test that action_repair_done creates a new
        stock move for the repaired product."""
        self.stock_move.state = "done"
        self.repair_order._compute_product_location_dest_id()

        self.repair_order.action_repair_done()

        transfer_move_name = f"Transfer After Repair - {self.repair_order.name}"
        new_move = self.env["stock.move"].search([("name", "=", transfer_move_name)])

        self.assertTrue(
            new_move,
            "A new stock move should be created for the "
            "transfer of the repaired product.",
        )
        self.assertEqual(
            new_move.location_dest_id,
            self.repair_order.product_location_dest_id,
            "The new stock move's location_dest_id should match "
            "the repair order's product_location_dest_id.",
        )
