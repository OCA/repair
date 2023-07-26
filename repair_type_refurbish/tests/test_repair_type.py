# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import TransactionCase


class TestRepairType(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestRepairType, self).setUp(*args, **kwargs)

        # First of all we create a repair to work with
        self.repair_r1 = self.env.ref("repair.repair_r1")

        # Then, we create a repair type to know the source and destination locations
        self.repair_type_1 = self.env["repair.type"].create(
            {
                "name": "Repairings refurbish to components",
                "source_location_id": self.env.ref("stock.stock_location_stock").id,
                "refurbish_location_dest_id": self.env.ref(
                    "stock.stock_location_components"
                ).id,
            }
        )
        self.repair_type_2 = self.env["repair.type"].create(
            {
                "name": "Repairings refurbsih in stock",
                "refurbish_location_dest_id": self.env.ref(
                    "stock.stock_location_stock"
                ).id,
                "source_location_id": self.env.ref(
                    "stock.stock_location_components"
                ).id,
            }
        )

    def test_compute_refurbish_location_id(self):
        # First we associate the repair with the repair type
        self.repair_r1.repair_type_id = self.repair_type_1

        # Afterwards we will assert the source and
        # destination of the product in the repair order
        self.assertEqual(
            self.repair_r1.refurbish_location_dest_id,
            self.repair_type_1.refurbish_location_dest_id,
        )

        # We change the repair type to repair_type_2 and check if all the locations changed
        self.repair_r1.repair_type_id = self.repair_type_2

        self.assertEqual(
            self.repair_r1.refurbish_location_dest_id,
            self.repair_type_2.refurbish_location_dest_id,
        )
