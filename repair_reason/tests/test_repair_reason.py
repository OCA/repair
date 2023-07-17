# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestRepair(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.Repair = self.env["repair.order"]
        self.company = self.env.ref("base.main_company")
        self.product = self.env.ref("product.product_product_4")
        self.stock_location_stock = self.env.ref("stock.stock_location_stock")
        self.repair_reason = self.env["repair.reason"].create(
            {
                "name": "Testing Reason",
                "sequence": 100,
                "active": True,
                "company_id": self.company.id,
            }
        )

    def test_repair_reason(self):
        repair_order_form = Form(self.Repair)
        repair_order_form.product_id = self.product
        repair_order_form.location_id = self.stock_location_stock
        repair_order_form.repair_reason_id = self.repair_reason
        repair_order = repair_order_form.save()
        self.assertEqual(
            repair_order.repair_reason_id,
            self.repair_reason,
            "Repair order's repair_reason_id not set correctly.",
        )
