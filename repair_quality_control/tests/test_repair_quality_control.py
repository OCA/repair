# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class RepairQualityControlTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repair_order = cls.env["repair.order"].create(
            {
                "product_id": cls.env.ref("product.product_product_27").id,
                "lot_id": cls.env.ref("stock.lot_product_27").id,
            }
        )

    def test_create_inspection_from_repair_order(self):
        inspect_form = Form(
            self.env["qc.inspection"].with_context(
                default_repair_id=self.repair_order.id,
                default_object_id=f"product.product,{self.repair_order.product_id.id}",
            )
        )
        qc_inspection = inspect_form.save()
        self.assertEqual(self.repair_order.inspection_ids, qc_inspection)
        self.assertEqual(
            self.repair_order.inspection_ids.product_id, qc_inspection.product_id
        )
        self.repair_order.lot_id = self.env.ref("stock.lot_product_27").id
        inspect_form = Form(
            self.env["qc.inspection"].with_context(
                default_repair_id=self.repair_order.id,
                default_object_id=f"stock.lot,{self.repair_order.lot_id.id}",
            )
        )
        qc_inspection = inspect_form.save()
        self.assertEqual(self.repair_order.inspection_ids[1], qc_inspection)
        self.assertEqual(
            self.repair_order.inspection_ids[1].product_id, qc_inspection.product_id
        )
        self.assertEqual(
            self.repair_order.inspection_ids[1].lot_id, qc_inspection.lot_id
        )
