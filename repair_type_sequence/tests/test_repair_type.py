# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestRepairType(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestRepairType, self).setUp(*args, **kwargs)

        # add repair model
        self.repair_model = self.env["repair.order"]
        # the product to use
        self.product = self.env.ref("product.product_product_4")
        # Then, we create a repair type to know the source and destination locations
        self.repair_type_1 = self.env["repair.type"].create(
            {
                "name": "Repair type 1",
                "source_location_id": self.env.ref("stock.stock_location_stock").id,
                "sequence_prefix": "RTT1",
            }
        )
        self.repair_type_2 = self.env["repair.type"].create(
            {
                "name": "Repair type 2",
                "source_location_id": self.env.ref("stock.stock_location_stock").id,
                "sequence_prefix": "RTT2",
            }
        )

    def test_repair_type_sequence(self):
        # First we check the creation
        repair_order_form = Form(self.repair_model)
        repair_order_form.product_id = self.product
        repair_order_form.repair_type_id = self.repair_type_1
        repair_order = repair_order_form.save()
        self.assertTrue(self.repair_type_1.sequence_prefix in repair_order.name)
        # Afterwards we check the write
        repair_order.repair_type_id = self.repair_type_2
        self.assertTrue(self.repair_type_2.sequence_prefix in repair_order.name)
