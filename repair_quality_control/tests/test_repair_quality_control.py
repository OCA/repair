# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class RepairQualityControlTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_tmpl = cls.env.ref("product.product_product_27").product_tmpl_id
        cls.product = cls.product_tmpl.product_variant_id
        cls.test = cls.env.ref("quality_control_oca.qc_test_1")
        cls.trigger = cls.env.ref("repair_quality_control.qc_trigger_repair")
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.repair_order = cls.env["repair.order"].create(
            {
                "product_id": cls.product.id,
                "lot_id": cls.env.ref("stock.lot_product_27").id,
                "invoice_method": "none",
                "partner_id": cls.partner.id,
            }
        )
        cls.env.company.repair_auto_generate_qc_inspection = True
        cls.env.company.repair_generate_qc_inspection_state = "confirmed"

    def test_qc_inspection_compute(self):
        # Check that the repair_id, product_id and lot_id are not set
        # since inspection does not have an object_id
        inspect_form = Form(self.env["qc.inspection"])
        qc_inspection = inspect_form.save()
        self.assertFalse(qc_inspection.repair_id)
        self.assertFalse(qc_inspection.product_id)
        self.assertFalse(qc_inspection.lot_id)
        # Set the object_id to a repair order and check that the
        # repair_id, product_id and lot_id are set
        qc_inspection.write({"object_id": f"repair.order,{self.repair_order.id}"})
        self.assertEqual(qc_inspection.repair_id, self.repair_order)
        self.assertEqual(qc_inspection.product_id, self.repair_order.product_id)
        self.assertEqual(qc_inspection.lot_id, self.repair_order.lot_id)

    def test_compute_show_button_create_qc_inspection(self):
        # Show_button_create_qc_inspection is set to True
        # on RO confirmation
        self.env.company.repair_auto_generate_qc_inspection = False
        self.env.company.repair_generate_qc_inspection_state = "confirmed"
        self.repair_order.action_validate()
        self.assertEqual(self.repair_order.state, "confirmed")
        self.assertTrue(self.repair_order.show_button_create_qc_inspection)
        # If we set the generate_qc_inspection_state to 'done'
        # the button should not be shown anymore
        self.env.company.repair_generate_qc_inspection_state = "done"
        self.assertFalse(self.repair_order.show_button_create_qc_inspection)
        # Now, the RO will be done and the button should be shown
        # again
        self.repair_order.action_repair_start()
        self.repair_order.action_repair_end()
        self.assertEqual(self.repair_order.state, "done")
        self.assertTrue(self.repair_order.show_button_create_qc_inspection)
        # If we auto generate the inspection, the button should never
        # be shown
        self.env.company.repair_auto_generate_qc_inspection = True
        self.assertFalse(self.repair_order.show_button_create_qc_inspection)

    def test_repair_cancel(self):
        inspect_form = Form(
            self.env["qc.inspection"].with_context(
                default_object_id=f"repair.order,{self.repair_order.id}",
                default_test=False,
            )
        )
        qc_inspection_1 = inspect_form.save()
        qc_inspection_2 = qc_inspection_1.copy()
        qc_inspection_1.test = self.env.ref("quality_control_oca.qc_test_1").id
        qc_inspection_1.action_todo()
        self.assertEqual(qc_inspection_1.state, "ready")
        self.assertEqual(qc_inspection_2.state, "draft")
        self.assertEqual(len(self.repair_order.inspection_ids), 2)
        # After cancelling, the draft inspection should be deleted
        # and the other one should be cancelled
        self.repair_order.action_repair_cancel()
        self.assertEqual(len(self.repair_order.inspection_ids), 1)
        self.assertNotIn(self.repair_order.inspection_ids, qc_inspection_2)
        self.assertIn(self.repair_order.inspection_ids, qc_inspection_1)
        self.assertEqual(qc_inspection_1.state, "canceled")

    def test_create_inspection_from_repair_order(self):
        # Create an inspection from a repair order, with all the fields
        # and check that the inspection is created accordingly
        inspect_form = Form(
            self.env["qc.inspection"].with_context(
                default_object_id=f"repair.order,{self.repair_order.id}"
            )
        )
        qc_inspection = inspect_form.save()
        self.assertEqual(self.repair_order.inspection_ids, qc_inspection)
        self.assertEqual(
            self.repair_order.inspection_ids.product_id, qc_inspection.product_id
        )
        self.assertEqual(self.repair_order.inspection_ids.lot_id, qc_inspection.lot_id)
        # Create an inspection from a repair order, without the lot_id
        # and check that the inspection is created accordingly
        self.repair_order.lot_id = False
        inspect_form = Form(
            self.env["qc.inspection"].with_context(
                default_object_id=f"repair.order,{self.repair_order.id}"
            )
        )
        qc_inspection = inspect_form.save()
        self.assertEqual(self.repair_order.inspection_ids[1], qc_inspection)
        self.assertEqual(
            self.repair_order.inspection_ids[1].product_id, qc_inspection.product_id
        )
        self.assertFalse(
            self.repair_order.inspection_ids[1].lot_id, qc_inspection.lot_id
        )

    def test_inspection_create_for_product(self):
        # Create an inspection for a product and check that the inspection
        # is created accordingly. It needs to be created on confirmation
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_validate()
        self.assertEqual(self.repair_order.state, "confirmed")
        self.assertEqual(len(self.repair_order.inspection_ids), 1)
        self.assertEqual(self.repair_order.inspection_ids.test, self.test)

    def test_inspection_create_for_product_on_done(self):
        # Create an inspection for a product and check that the inspection
        # is created accordingly. It needs to be created on done
        self.env.company.repair_generate_qc_inspection_state = "done"
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_validate()
        self.assertEqual(self.repair_order.state, "confirmed")
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_repair_start()
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_repair_end()
        self.assertEqual(self.repair_order.state, "done")
        self.assertEqual(len(self.repair_order.inspection_ids), 1)
        self.assertEqual(self.repair_order.inspection_ids.test, self.test)

    def test_inspection_no_create_for_product(self):
        # Do not create an inspection since the company is not configured
        # to auto generate inspections
        self.env.company.repair_auto_generate_qc_inspection = False
        self.product.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_validate()
        self.assertEqual(self.repair_order.state, "confirmed")
        self.assertEqual(len(self.repair_order.inspection_ids), 0)

    def test_inspection_create_for_template(self):
        self.product_tmpl.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_validate()
        self.assertEqual(len(self.repair_order.inspection_ids), 1)
        self.assertEqual(self.repair_order.inspection_ids.test, self.test)

    def test_inspection_create_for_category(self):
        self.product.categ_id.qc_triggers = [
            (0, 0, {"trigger": self.trigger.id, "test": self.test.id})
        ]
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_validate()
        self.assertEqual(self.repair_order.state, "confirmed")
        self.assertEqual(len(self.repair_order.inspection_ids), 1)
        self.assertEqual(self.repair_order.inspection_ids.test, self.test)

    def test_inspection_create_for_category_partner(self):
        self.product.categ_id.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": self.partner.ids,
                },
            )
        ]
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_validate()
        self.assertEqual(self.repair_order.state, "confirmed")
        self.assertEqual(len(self.repair_order.inspection_ids), 1)
        self.assertEqual(self.repair_order.inspection_ids.test, self.test)

    def test_inspection_create_for_category_wrong_partner(self):
        wrong_partner = self.env.ref("base.res_partner_2")
        self.product.categ_id.qc_triggers = [
            (
                0,
                0,
                {
                    "trigger": self.trigger.id,
                    "test": self.test.id,
                    "partners": wrong_partner.ids,
                },
            )
        ]
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
        self.repair_order.action_validate()
        self.assertEqual(self.repair_order.state, "confirmed")
        self.assertEqual(len(self.repair_order.inspection_ids), 0)
