# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairOrderProductByLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Product = cls.env["product.product"]
        cls.Lot = cls.env["stock.lot"]
        cls.RepairOrder = cls.env["repair.order"]

        # Create product
        cls.product = cls.Product.create(
            {
                "name": "Test Product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "uom_po_id": cls.env.ref("uom.product_uom_unit").id,
                "tracking": "serial",
            }
        )

        # Create lot
        cls.lot = cls.Lot.create(
            {
                "name": "SN-001",
                "product_id": cls.product.id,  # ← ВОТ ТУТ ИСПРАВЛЕНИЕ
                "company_id": cls.env.company.id,
            }
        )

    def test_onchange_lot_sets_product(self):
        """Test onchange sets product when lot is selected."""
        order = self.env["repair.order"].new({})
        order.lot_id = self.lot
        order._onchange_lot_id_set_product()
        self.assertEqual(order.product_id, self.product)

    def test_onchange_clears_product(self):
        """Test onchange clears product when lot is removed."""
        order = self.env["repair.order"].new(
            {
                "lot_id": self.lot.id,
                "product_id": self.product.id,
            }
        )
        order.lot_id = False
        order._onchange_lot_id_set_product()
        self.assertFalse(order.product_id)

    def test_new_record_workflow(self):
        """Test complete workflow with new record."""
        order = self.env["repair.order"].new({"name": "Test Repair"})
        order.lot_id = self.lot
        order._onchange_lot_id_set_product()
        self.assertEqual(order.product_id, self.product)
        vals = order._convert_to_write(order._cache)
        saved_order = self.env["repair.order"].create(vals)
        self.assertEqual(saved_order.product_id, self.product)
        self.assertEqual(saved_order.lot_id, self.lot)
