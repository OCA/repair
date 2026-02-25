# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestRepairWarehouse(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Repair Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "product to repair", "type": "product"}
        )
        cls.wh1 = cls.env["stock.warehouse"].create({"name": "WH1", "code": "W1"})
        cls.wh2 = cls.env["stock.warehouse"].create({"name": "WH2", "code": "W2"})
        cls.loc1 = cls.env["stock.location"].create(
            {
                "name": "Repair Loc 1",
                "usage": "internal",
                "location_id": cls.wh1.view_location_id.id,
            }
        )
        cls.loc2 = cls.env["stock.location"].create(
            {
                "name": "Repair Loc 2",
                "usage": "internal",
                "location_id": cls.wh2.view_location_id.id,
            }
        )

    def _create_repair(self, **vals):
        base = {
            "partner_id": self.partner.id,
            "product_id": self.product.id,
            "location_id": self.loc1.id,
        }
        base.update(vals)
        return self.env["repair.order"].create(base)

    def test_01_location_computes_warehouse(self):
        repair = self._create_repair(location_id=self.loc1.id)
        self.assertEqual(repair.warehouse_id, self.wh1)
        repair.location_id = self.loc2
        self.assertEqual(repair.warehouse_id, self.wh2)

    def test_03_manual_mismatch_raises_on_write(self):
        repair = self._create_repair(location_id=self.loc1.id)
        with self.assertRaises(ValidationError):
            repair.write({"warehouse_id": self.wh2.id})

    def test_04_allow_manual_warehouse_when_location_empty(self):
        repair = self._create_repair(location_id=self.loc1.id)
        repair.write({"location_id": False})
        repair.write({"warehouse_id": self.wh2.id})
        self.assertEqual(repair.warehouse_id, self.wh2)
