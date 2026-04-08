# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairCustomSender(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test Partner", "email": "test@example.com"}
        )
        cls.repair_order = cls.env["repair.order"].create(
            {
                "partner_id": cls.partner.id,
                "product_id": cls.env.ref("product.product_product_3").id,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.custom_email = "support@mycompany.com"

    def test_setting_off_default_behavior(self):
        """Test with setting OFF: sender should be the current user (OdooBot in tests)"""
        self.env.company.use_custom_repair_sender = False

        action = self.repair_order.action_send_mail()
        composer = (
            self.env["mail.compose.message"]
            .with_context(**action["context"])
            .create({})
        )
        _, result_messages = composer._action_send_mail()
        self.assertEqual(result_messages.email_from, self.env.user.email_formatted)

    def test_setting_on_custom_behavior(self):
        """Test with setting ON: sender should be the custom email from settings"""
        self.env.company.use_custom_repair_sender = True
        self.env.company.repair_custom_email_from = "test@testing.com"
        action = self.repair_order.action_send_mail()
        composer = (
            self.env["mail.compose.message"]
            .with_context(**action["context"])
            .create({})
        )
        result_mails_su, result_messages = composer._action_send_mail()
        self.assertEqual(result_messages.email_from, "test@testing.com")
