# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairManufacturer(TransactionCase):
    """Test suite for manufacturer tracking in repair order"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
