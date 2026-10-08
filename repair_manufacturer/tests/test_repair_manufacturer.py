# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairManufacturer(TransactionCase):
    """Test suite for manufacturer tracking and filtering in repair order"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test partners
        cls.apple = cls.env["res.partner"].create(
            {
                "name": "Apple",
                "is_manufacturer": True,
            }
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "is_manufacturer": False,
            }
        )

        cls.cat_phones = cls.env["product.category"].create({"name": "Smartphones"})
        cls.cat_laptops = cls.env["product.category"].create({"name": "Laptops"})

        cls.product_iphone = cls.env["product.product"].create(
            {
                "name": "iPhone",
                "type": "service",
                "categ_id": cls.cat_phones.id,
                "manufacturer_id": cls.apple.id,
            }
        )
        cls.product_other = cls.env["product.product"].create(
            {
                "name": "Generic Item",
                "type": "service",
                "categ_id": cls.cat_laptops.id,
            }
        )

    def test_01_partner_is_manufacturer_flag(self):
        self.assertTrue(self.apple.is_manufacturer)
        self.assertFalse(self.customer.is_manufacturer)

    def test_02_repair_order_manufacturer_assignment(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.customer.id,
                "manufacturer_id": self.apple.id,
            }
        )
        self.assertEqual(repair.manufacturer_id, self.apple)
        self.assertEqual(repair.partner_id, self.customer)

    def test_03_allowed_categories_computation(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.customer.id,
                "manufacturer_id": self.apple.id,
            }
        )
        repair._compute_allowed_category_ids()
        # Should include Apple's category, but exclude unassigned categories
        self.assertIn(self.cat_phones, repair.allowed_category_ids)
        self.assertNotIn(self.cat_laptops, repair.allowed_category_ids)

    def test_04_onchange_resets(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.customer.id,
                "manufacturer_id": self.apple.id,
                "category_id": self.cat_phones.id,
                "product_id": self.product_iphone.id,
            }
        )

        repair.manufacturer_id = False
        repair._onchange_manufacturer_id()
        self.assertFalse(repair.category_id)
        self.assertFalse(repair.product_id)
