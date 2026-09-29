# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestRepairTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a product with lot/serial tracking
        cls.product_with_lot = cls.env["product.product"].create(
            {
                "name": "Product with lot tracking",
                "type": "product",
                "tracking": "lot",
                "list_price": 10.0,
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )
        cls.lot_id = cls.env["stock.lot"].create(
            {
                "name": "LOT0001",
                "product_id": cls.product_with_lot.id,
                "company_id": cls.env.company.id,
            }
        )

        # Create unique repair orders
        cls.repair_r1 = cls.env["repair.order"].create(
            {
                "product_id": cls.product_with_lot.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "lot_id": cls.lot_id.id,
                "product_qty": 5.0,
            }
        )
        cls.repair_r2 = cls.env["repair.order"].create(
            {
                "product_id": cls.product_with_lot.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "lot_id": cls.lot_id.id,
                "product_qty": 1.0,
            }
        )
        cls.repair_order_no_product = cls.env["repair.order"].create(
            {
                "location_id": cls.env.ref("stock.stock_location_stock").id,
            }
        )

        # Create a destination location
        cls.stock_location_destination = cls.env["stock.location"].create(
            {"name": "Destination Locations", "usage": "internal"}
        )

        # Add stock for repair orders
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product_with_lot.id,
                "lot_id": cls.lot_id.id,
                "location_id": cls.repair_r1.location_id.id,
                "quantity": 5.0,
            }
        )

        # Set the repair auto-transfer configuration to disabled (manual transfers)
        cls.env["ir.config_parameter"].set_param("repair.auto_transfer_repair", False)

    def setUpRepairOrder(self, repair_order):
        # Validate and set the state of the repair order
        repair_order.action_validate()
        self.assertEqual(repair_order.state, "confirmed")
        repair_order.action_repair_start()
        self.assertEqual(repair_order.state, "under_repair")
        repair_order.action_repair_end()
        self.assertEqual(repair_order.state, "done")

    def createTransfer(self, repair_order, quantity):
        # Create and execute a transfer wizard
        transfer_repair_wizard = self.env["repair.move.transfer"].create(
            {
                "repair_order_id": repair_order.id,
                "quantity": quantity,
                "location_dest_id": self.stock_location_destination.id,
                "remaining_quantity": repair_order.remaining_quantity,
            }
        )
        transfer_repair_wizard.action_create_transfer()

    def test_repair_transfer_manual_1(self):
        """Test creating a single manual transfer."""
        self.setUpRepairOrder(self.repair_r1)
        self.createTransfer(self.repair_r1, 1.0)
        self.assertEqual(len(self.repair_r1.picking_ids), 1)

    def test_repair_transfer_manual_multiple(self):
        """Test multiple manual transfers for the repair order."""
        self.setUpRepairOrder(self.repair_r1)

        # Attempt to create a transfer for 0 items.
        with self.assertRaises(
            UserError, msg="Quantity to transfer must be greater than 0."
        ):
            self.createTransfer(self.repair_r1, 0.0)

        # Create the first manual transfer for 1 item
        self.createTransfer(self.repair_r1, 1.0)

        # Update remaining quantity after first transfer
        self.repair_r1._compute_remaining_quantity()

        # Create the second transfer for 2 items
        self.createTransfer(self.repair_r1, 2.0)

        # Update remaining quantity after second transfer
        self.repair_r1._compute_remaining_quantity()

        # Attempt to create a third transfer for 3 items,
        # which exceeds the remaining quantity (which is now 2)
        with self.assertRaises(
            UserError,
            msg="Quantity to transfer cannot exceed the remaining "
            "quantity in the repair order.",
        ):
            self.createTransfer(self.repair_r1, 3.0)

        # Check the number of pickings created
        self.assertEqual(len(self.repair_r1.picking_ids), 2)

        # Check the total quantity transferred
        total_transferred = sum(
            qty
            for picking in self.repair_r1.picking_ids
            for qty in picking.move_ids.mapped("product_uom_qty")
        )
        self.assertEqual(
            total_transferred, 3.0, "Total transferred quantity should equal to 3.0"
        )

    def test_repair_transfer_automatic(self):
        """Test automatic transfer creation upon repair order completion."""
        self.env["ir.config_parameter"].set_param("repair.auto_transfer_repair", True)
        self.setUpRepairOrder(self.repair_r2)
        self.assertEqual(len(self.repair_r2.picking_ids), 1)
        self.assertEqual(self.repair_r2.picking_ids.state, "done")

    def test_repair_transfer_automatic_no_product(self):
        self.env["ir.config_parameter"].set_param("repair.auto_transfer_repair", True)
        with self.assertRaises(ValidationError):
            self.repair_order_no_product.action_validate()

    def test_repair_transfer_no_reservation(self):
        """Do not crash when the transfer move can't reserve any quant.

        If the quantity to transfer is already reserved by another stock
        operation, action_assign() creates no move line on the transfer,
        so setting the lot on move_line_ids[0] used to raise
        IndexError: tuple index out of range.
        """
        self.setUpRepairOrder(self.repair_r1)

        # Reserve away all the available stock with an unrelated move, so
        # the transfer wizard's own move can't reserve anything.
        competing_move = self.env["stock.move"].create(
            {
                "name": "Competing reservation",
                "product_id": self.product_with_lot.id,
                "location_id": self.repair_r1.location_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "product_uom_qty": 5.0,
                "product_uom": self.product_with_lot.uom_id.id,
            }
        )
        competing_move._action_confirm()
        competing_move._action_assign()
        self.assertEqual(competing_move.state, "assigned")

        # No quantity left free to reserve: action_assign() creates no
        # move line on the transfer, and this call must not raise.
        self.createTransfer(self.repair_r1, 1.0)
        self.assertEqual(len(self.repair_r1.picking_ids), 1)
