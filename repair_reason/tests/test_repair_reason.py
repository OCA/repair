# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestRepair(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Repair = cls.env["repair.order"]
        cls.company = cls.env.ref("base.main_company")
        cls.picking_type = cls.env.ref("repair.picking_type_warehouse0_repair")
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.repair_reason = cls.env["repair.reason"].create(
            {
                "name": "Testing Reason",
                "sequence": 100,
                "active": True,
                "company_id": cls.company.id,
            }
        )

    def test_repair_reason(self):
        repair_order_form = Form(
            self.Repair.with_context(default_picking_type_id=self.picking_type.id)
        )
        repair_order_form.product_id = self.product
        repair_order_form.repair_reason_id = self.repair_reason
        repair_order = repair_order_form.save()
        self.assertEqual(
            repair_order.repair_reason_id,
            self.repair_reason,
            "Repair order's repair_reason_id not set correctly.",
        )
