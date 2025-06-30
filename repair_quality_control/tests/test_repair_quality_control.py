# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class RepairQualityControlTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env.ref("product.product_product_27")
        cls.lot = cls.env.ref("stock.lot_product_27")

        cls.repair_order = cls.env["repair.order"].create(
            {
                "product_id": cls.product.id,
                "lot_id": cls.lot.id,
            }
        )

    def test_create_inspection_from_repair_order(self):
        inspect_form = Form(
            self.env["qc.inspection"].with_context(
                default_repair_id=self.repair_order.id,
                default_object_id=f"product.product, {self.repair_order.product_id.id}",
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
                default_object_id=f"stock.lot, {self.repair_order.lot_id.id}",
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

    def test_create_repair_order_from_inspection(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": self.env.ref("stock.stock_location_customers").id,
                "location_dest_id": self.env.ref("stock.stock_location_stock").id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
            }
        )
        qc_inspection = self.env["qc.inspection"].create(
            {
                "picking_id": picking.id,
                "object_id": f"stock.move, {move.id}",
                "product_id": self.product.id,
                "lot_id": self.lot.id,
            }
        )
        repair = qc_inspection.action_repair()
        repair_form = Form(
            self.env[(repair.get("res_model"))].with_context(**repair["context"])
        )
        repair = repair_form.save()
        self.assertEqual(repair.move_id, move)
        self.assertEqual(repair.lot_id, qc_inspection.lot_id)
        self.assertEqual(repair.product_id, qc_inspection.product_id)
