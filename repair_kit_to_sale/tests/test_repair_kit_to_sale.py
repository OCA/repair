import logging

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestRepairKitToSale(TransactionCase):
    def setUp(self):
        super().setUp()
        self.RepairOrder = self.env["repair.order"]
        self.Partner = self.env["res.partner"]
        self.Product = self.env["product.product"]
        self.StockLocation = self.env["stock.location"]
        self.StockLot = self.env["stock.lot"]
        self.StockMove = self.env["stock.move"]
        self.StockMoveLine = self.env["stock.move.line"]
        self.SaleOrder = self.env["sale.order"]
        self.SaleOrderLine = self.env["sale.order.line"]
        self.MrpBom = self.env["mrp.bom"]
        self.MrpBomLine = self.env["mrp.bom.line"]

        # Create your repair order, linking it to the sale order
        self.repair_order = self.RepairOrder.create(
            {
                "name": "Test Repair Order",
                "partner_id": self.Partner.create({"name": "Test Partner"}).id,
            }
        )

        # Create a kit product
        self.product_kit = self.Product.create(
            {
                "name": "Test Kit Product",
                "type": "product",
            }
        )

        # Create a component product
        self.component_product = self.Product.create(
            {
                "name": "Test Component",
                "type": "product",
            }
        )

        # Create stock locations
        self.location_origin = self.StockLocation.create(
            {"name": "Test Origin Location"}
        )
        self.location_dest = self.StockLocation.create(
            {"name": "Test Destination Location"}
        )

        # Create a phantom BOM for the kit
        self.bom = self.MrpBom.create(
            {
                "product_tmpl_id": self.product_kit.product_tmpl_id.id,
                "type": "phantom",
                "product_qty": 1.0,
            }
        )
        self.bom_line = self.MrpBomLine.create(
            {
                "bom_id": self.bom.id,
                "product_id": self.component_product.id,
                "product_qty": 2.0,
            }
        )

        # Create a default stock move
        self.stock_move = self._create_stock_move(
            name="Test Stock Move",
            product_id=self.component_product.id,
            product_uom_qty=2.0,  # Matches 2.0 * kit_original_qty=1 => a "full kit"
            kit_original_qty=1.0,
            price_unit=100.0,
            origin="Test Origin",
        )

    def _create_stock_move(self, **kwargs):
        """
        Helper to create stock moves with a default set of values.
        Allows overriding fields by passing them as kwargs.
        """
        default_vals = {
            "product_id": self.component_product.id,
            "bom_line_id": self.bom_line.id,
            "repair_id": self.repair_order.id,
            "location_id": self.location_origin.id,
            "location_dest_id": self.location_dest.id,
        }
        default_vals.update(kwargs)
        return self.StockMove.create(default_vals)

    def test_01_write_split_stock_move(self):
        """Test that increasing product_uom_qty beyond the BoM limit splits the move."""
        self.assertEqual(self.stock_move.product_uom_qty, 2.0)
        self.assertEqual(self.stock_move.kit_original_qty, 1.0)

        # Increase beyond the BoM limit: 2.0 => 5.0
        self.stock_move.write({"product_uom_qty": 5.0})

        # Fetch all moves created for this repair order
        all_moves = self.StockMove.search(
            [("repair_id", "=", self.repair_order.id)], order="id asc"
        )
        self.assertEqual(len(all_moves), 2, "Should have original + 1 surplus move.")

        original_move, surplus_move = all_moves[0], all_moves[1]

        # Original move should be capped at 2.0
        self.assertEqual(original_move.product_uom_qty, 2.0)
        # Surplus move carries 3.0
        self.assertEqual(surplus_move.product_uom_qty, 3.0)
        self.assertFalse(
            surplus_move.bom_line_id, "Surplus shouldn't carry the BoM line"
        )
        self.assertFalse(
            surplus_move.kit_original_qty, "Surplus shouldn't carry kit_original_qty"
        )

    def test_02_prepare_phantom_line_vals_includes_bom_line_id(self):
        """
        Ensure _prepare_phantom_line_vals includes 'bom_line_id' and sets
        'kit_original_qty' if the bom_line has a valid bom_id.
        """
        vals_with_bom = self.stock_move._prepare_phantom_line_vals(
            self.bom_line, qty=5.0
        )

        self.assertEqual(
            vals_with_bom.get("bom_line_id"),
            self.bom_line.id,
            "Should include the bom_line_id in the returned vals",
        )
        self.assertEqual(
            vals_with_bom.get("kit_original_qty"),
            self.stock_move.product_uom_qty,
            "Should copy the move's product_uom_qty to kit_original_qty",
        )

    def test_03_can_form_full_kit_multiple_moves(self):
        """
        Verify _can_form_full_kit returns True when multiple moves match the required
        BOM-line quantities for the same kit, and False otherwise.
        """
        # 1) Create a second component product.
        product_second_component = self.Product.create(
            {
                "name": "Second Component",
                "type": "product",
            }
        )

        # 2) Add a second BOM line to the existing phantom BOM.
        #    Let's say we need 3.0 units of this second component (for 1 'kit').
        second_bom_line = self.MrpBomLine.create(
            {
                "bom_id": self.bom.id,
                "product_id": product_second_component.id,
                "product_qty": 3.0,
            }
        )

        # 3) Create two moves that collectively form the full kit:
        #    - First move: covers the original component, 2.0 units
        #    - Second move: covers the new component, 3.0 units
        #    Both use kit_original_qty=1.0, meaning 1 full kit.
        move1 = self._create_stock_move(
            name="Move for First Component",
            product_id=self.component_product.id,
            product_uom_qty=2.0,  # matches 2.0 * kit_original_qty=1.0
            kit_original_qty=1.0,
            bom_line_id=self.bom_line.id,
        )
        move2 = self._create_stock_move(
            name="Move for Second Component",
            product_id=product_second_component.id,
            product_uom_qty=3.0,  # matches 3.0 * kit_original_qty=1.0
            kit_original_qty=1.0,
            bom_line_id=second_bom_line.id,
        )

        # Combine the two moves in a recordset
        combined_moves = move1 | move2

        # 4) Check that we can form a full kit
        self.assertTrue(
            move1._can_form_full_kit(combined_moves),
            "Should return True because each move matches the needed BOM quantity "
            "for 1 kit.",
        )

        # 5) Now "break" one move's quantity so it no longer forms a complete kit
        move2.write({"product_uom_qty": 2.0})  # less than the required 3.0
        self.assertFalse(
            move1._can_form_full_kit(combined_moves),
            "Should return False when one move doesn't match its BOM requirement.",
        )

    def test_04_action_create_sale_order_full_kit(self):
        """
        Simulate multiple stock moves that together form a full kit, then call
        action_create_sale_order. Confirm we get one kit line that references
        both moves.
        """
        # 1) Ensure the Repair has no existing sale order, and it has a partner.
        self.assertFalse(
            self.repair_order.sale_order_id,
            "Repair shouldn't already have a Sale Order before calling "
            "action_create_sale_order.",
        )
        self.assertTrue(
            self.repair_order.partner_id,
            "Repair must have a partner to be able to create a Sale Order.",
        )

        # 2) Create a second component product and a second BOM line for the kit.
        product_second_component = self.Product.create(
            {
                "name": "Second Component",
                "type": "product",
            }
        )
        second_bom_line = self.MrpBomLine.create(
            {
                "bom_id": self.bom.id,
                "product_id": product_second_component.id,
                "product_qty": 3.0,  # We need 3 units of this second product per 1 kit
            }
        )

        # 3) Create two moves referencing each BOM line, each with
        #    repair_line_type="add"
        #    so they get processed in _create_repair_sale_order_line.
        #    Both moves have kit_original_qty=1.0, so we want:
        #       - Move1: 2.0 units for the first BOM line
        #       - Move2: 3.0 units for the second BOM line
        move1 = self._create_stock_move(
            name="Move for First BOM line",
            bom_line_id=self.bom_line.id,
            product_id=self.component_product.id,
            product_uom_qty=2.0,
            kit_original_qty=1.0,
            price_unit=50.0,  # Might differ from the other move
            repair_line_type="add",
        )
        move2 = self._create_stock_move(
            name="Move for Second BOM line",
            bom_line_id=second_bom_line.id,
            product_id=product_second_component.id,
            product_uom_qty=3.0,
            kit_original_qty=1.0,
            price_unit=60.0,
            repair_line_type="add",
        )

        # 4) Now we call the standard flow: user clicks "Create Quotation"
        # on the Repair form.
        action = self.repair_order.action_create_sale_order()
        self.assertEqual(action["res_model"], "sale.order")
        self.assertIn(
            "res_id",
            action,
            "Action should contain 'res_id' of the created sale order.",
        )

        # Refresh the repair order, which should now have a sale_order_id
        self.assertTrue(
            self.repair_order.sale_order_id,
            "A new Sale Order should have been created and linked to the repair_order.",
        )

        # 5) Since the kit is "full"
        #    we expect exactly one Sale Order line referencing the kit product.
        so_line = self.SaleOrderLine.search(
            [("order_id", "=", self.repair_order.sale_order_id.id)], limit=1
        )
        self.assertTrue(
            so_line, "A sale order line should be created for the full kit."
        )

        # Check that the kit product is used
        self.assertEqual(
            so_line.product_id,
            self.product_kit.product_variant_id,
            "A single kit line should appear on the sale order.",
        )
        # The kit quantity = kit_original_qty = 1.0 from the moves
        self.assertEqual(so_line.product_uom_qty, 1.0)

        # 6) Verify that both moves are linked to this single sale order line
        self.assertIn(
            move1,
            so_line.move_ids,
            "Move1 should be linked to the kit sale order line.",
        )
        self.assertIn(
            move2,
            so_line.move_ids,
            "Move2 should be linked to the kit sale order line.",
        )

    def test_05_action_create_sale_order_partial_kit(self):
        """
        If the moves do NOT form a complete kit, they should be treated as
        standard moves. Hence, the created sale order line should be the
        component product (not the kit product).
        """
        # 1) Ensure the Repair has no existing sale order, and it has a partner.
        self.assertFalse(
            self.repair_order.sale_order_id,
            "Repair shouldn't already have a Sale Order before calling "
            "action_create_sale_order.",
        )
        self.assertTrue(
            self.repair_order.partner_id,
            "Repair must have a partner to be able to create a Sale Order.",
        )

        # 2) Create a "partial kit" move that doesn't exactly match the BOM's required
        #    qty. For instance, BOM requires 2.0, but we supply 3.0 => partial kit
        #    scenario.
        self._create_stock_move(
            name="Partial Move",
            product_uom_qty=3.0,  # mismatch vs 2.0
            kit_original_qty=1.0,
            price_unit=80.0,
            repair_line_type="add",  # Mark as 'add' so it's processed
        )

        # 3) Call the method that typically is triggered by the
        action = self.repair_order.action_create_sale_order()

        # 4) Verify the action dictionary: we should navigate to the newly
        self.assertEqual(action["res_model"], "sale.order")
        self.assertIn(
            "res_id",
            action,
            "The returned action should contain 'res_id' of the new sale order.",
        )

        # 5) The repair_order should now have a linked sale_order_id
        self.assertTrue(
            self.repair_order.sale_order_id,
            "A new Sale Order should have been created and linked to the repair_order.",
        )

        # 6) Since the kit is "partial", the code falls back to creating a standard line
        created_line = self.SaleOrderLine.search(
            [("order_id", "=", self.repair_order.sale_order_id.id)], limit=1
        )
        self.assertTrue(
            created_line,
            "A standard sale order line should be created for partial kits.",
        )

        # 7) Confirm this line is for the component product, NOT the kit product
        self.assertNotEqual(
            created_line.product_id,
            self.product_kit.product_variant_id,
            "With a partial kit, the sale order line should be the component "
            "product, not the kit product.",
        )

        # 8) Price should match the move's price_unit
        self.assertAlmostEqual(
            created_line.price_unit,
            80.0,
            msg="Expected the sale order line price to match the partial "
            "move's price_unit.",
        )

    def test_06_qty_delivered_full_kit_multiple_moves_after_repair_end(self):
        # 1) Add a second component + BOM line, so forming one kit requires:
        #    - 2.0 units of self.component_product (existing BOM line)
        #    - 3.0 units of product_second_component (new BOM line)
        product_second_component = self.Product.create(
            {
                "name": "Second Component",
                "type": "product",
            }
        )
        second_bom_line = self.MrpBomLine.create(
            {
                "bom_id": self.bom.id,
                "product_id": product_second_component.id,
                "product_qty": 3.0,
            }
        )

        # 2) Create two moves that collectively form one kit (kit_original_qty=1.0):
        #    - move1 for the first BOM line (needs 2.0)
        #    - move2 for the second BOM line (needs 3.0)
        move1 = self._create_stock_move(
            name="Kit Move 1 - Main Component",
            product_id=self.component_product.id,
            product_uom_qty=2.0,
            kit_original_qty=1.0,
            repair_line_type="add",
        )
        move2 = self._create_stock_move(
            name="Kit Move 2 - Second Component",
            product_id=product_second_component.id,
            product_uom_qty=3.0,
            kit_original_qty=1.0,
            repair_line_type="add",
            bom_line_id=second_bom_line.id,
        )

        # Attach both moves to the repair
        self.repair_order.write({"move_ids": [(4, move1.id), (4, move2.id)]})

        # 3) Create stock.move.line entries indicating both moves are fully processed:
        self.StockMoveLine.create(
            {
                "move_id": move1.id,
                "product_id": self.component_product.id,
                "quantity": 2.0,
                "location_id": self.location_origin.id,
                "location_dest_id": self.location_dest.id,
            }
        )
        self.StockMoveLine.create(
            {
                "move_id": move2.id,
                "product_id": product_second_component.id,
                "quantity": 3.0,
                "location_id": self.location_origin.id,
                "location_dest_id": self.location_dest.id,
            }
        )

        # 4) Validate & Create the sale order line
        self.repair_order.action_assign()
        self.repair_order.action_validate()
        self.repair_order.action_create_sale_order()
        self.assertTrue(
            self.repair_order.sale_order_id, "A sale order should be created."
        )

        # Grab the newly created sale order line
        so_line = self.SaleOrderLine.search(
            [("order_id", "=", self.repair_order.sale_order_id.id)], limit=1
        )
        self.assertTrue(so_line, "A kit sale order line should be created.")
        self.assertEqual(
            so_line.qty_delivered, 0.0, "No moves are done yet, so delivered=0."
        )

        # 5) Mark the repair as under repair, then end => sets moves to 'done'
        self.repair_order.action_repair_start()
        self.repair_order.action_repair_end()

        # 6) Now that both moves are 'done' with the correct quantities,
        #    the kit logic sees we can form exactly 1 kit => qty_delivered=1
        self.assertEqual(
            so_line.qty_delivered,
            1.0,
            "With 2.0 and 3.0 done for each BOM line, we form exactly 1 "
            "kit => delivered=1.",
        )
