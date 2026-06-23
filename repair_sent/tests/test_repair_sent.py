# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestRepairOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Repair Product",
                "type": "product",
            }
        )
        cls.product_consume = cls.env["product.product"].create(
            {
                "name": "Product To Consume",
                "type": "product",
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.repair_order = cls.env["repair.order"].create(
            {
                "partner_id": cls.partner.id,
                "product_id": cls.product.id,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.stock_location.id,
                "operations": [
                    Command.create(
                        {
                            "name": "spare parts",
                            "type": "add",
                            "price_unit": 100,
                            "product_id": cls.product_consume.id,
                            "product_uom_qty": 2.0,
                            "location_id": cls.stock_location.id,
                        }
                    )
                ],
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_location, 1.0
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_consume, cls.stock_location, 10.0
        )

    def _send_mail_via_wizard(self, repair_record):
        res = repair_record.action_send_mail()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})
        return wizard._action_send_mail()

    def test_updates_state_from_draft(self):
        self.assertEqual(self.repair_order.state, "draft")
        self.assertFalse(self.repair_order.quotation_sent)

        self._send_mail_via_wizard(self.repair_order)

        self.assertTrue(self.repair_order.quotation_sent)
        self.assertEqual(self.repair_order.state, "sent")

    def test_full_state_lifecyle(self):
        """Test the full flow from draft to done, ensuring state integrity."""
        self.assertEqual(self.repair_order.state, "draft")
        self.assertFalse(self.repair_order.quotation_sent)

        # 1. Draft -> Sent
        self._send_mail_via_wizard(self.repair_order)
        self.assertTrue(self.repair_order.quotation_sent)
        self.assertEqual(self.repair_order.state, "sent")

        # 2. Sent -> Confirmed
        self.repair_order.action_repair_confirm()
        self.assertEqual(self.repair_order.state, "confirmed")

        # 3. Confirmed -> Under Repair
        self.repair_order.action_repair_start()
        self.assertEqual(self.repair_order.state, "under_repair")

        # Ensure sending mail now doesn't revert state to 'sent'
        self._send_mail_via_wizard(self.repair_order)
        self.assertEqual(self.repair_order.state, "under_repair")

        # 4. Under Repair -> Done
        # action_repair_end() handles the completion of the work
        self.repair_order.action_repair_end()
        self.assertEqual(self.repair_order.state, "done")
