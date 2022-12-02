# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestRepairSaleORder(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestRepairSaleORder, self).setUp(*args, **kwargs)

    def test_01_repair_sale_order(self):
        # First of all we create a repair to work with
        repair_r1 = self.env.ref("repair.repair_r1")
        # Then, we create a repair type to know the source and destination locations
        repair_type_1 = self.env["repair.type"].create(
            {"name": "Sale repair type", "create_sale_order": True}
        )
        repair_r1.repair_type_id = repair_type_1
        # repair_r1.action_validate()
        repair_r1.action_create_sale_order()
        repair_r1._compute_sale_order()
        sale_order = repair_r1.sale_order_ids
        # Check the sale order is fine
        self.assertEqual(
            sale_order.order_line[0].product_id, repair_r1.operations.product_id
        )
        self.assertEqual(sale_order.order_line[0].price_unit, 50.0)
