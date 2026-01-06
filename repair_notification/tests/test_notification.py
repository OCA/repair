# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestNotification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Activate notifications
        cls.env.company.send_repair_start_confirmation = True
        cls.env.company.send_repair_end_confirmation = True

        # Partner
        cls.res_partner = cls.env["res.partner"].create({"name": "Wood Corner"})
        cls.res_partner_address = cls.env["res.partner"].create(
            {"name": "Willie Burke", "parent_id": cls.res_partner.id}
        )

        # Location
        cls.stock_warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.stock_location = cls.env["stock.location"].create(
            {
                "name": "Shelf 2",
                "location_id": cls.stock_warehouse.lot_stock_id.id,
            }
        )

        # Product
        cls.product_product = cls.env["product.product"].create(
            {"name": "Desk Combination", "type": "product"}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_product, cls.stock_location, 5
        )

        # Repair Order
        cls.repair = cls.env["repair.order"].create(
            {
                "address_id": cls.res_partner_address.id,
                "guarantee_limit": "2027-01-01",
                "invoice_method": "none",
                "user_id": False,
                "product_id": cls.product_product.id,
                "product_qty": 1.0,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "partner_invoice_id": cls.res_partner_address.id,
                "partner_id": cls.res_partner.id,
                "location_id": cls.stock_location.id,
            }
        )

        # Validate the repair order
        cls.repair.action_validate()

    def test_start_repair_notification(self):
        # Test case 1: Starting repair after order validation
        messages = self.repair.message_ids
        self.assertTrue(not self.repair.repair_start_mail_sent)
        self.repair.action_repair_start()
        new_messages = self.repair.message_ids - messages
        self.assertTrue(
            new_messages,
            "No message was posted on the repair order after starting repair",
        )
        self.assertTrue(self.repair.repair_start_mail_sent)

        # Test case 2: Starting repair after order cancellation -> Should not resend the email
        self.repair.action_repair_cancel()
        self.repair.action_repair_cancel_draft()
        self.repair.action_validate()
        self.repair.action_repair_start()
        self.assertTrue(self.repair.repair_start_mail_sent)

    def test_end_repair_notification(self):
        self.repair.action_repair_start()
        messages = self.repair.message_ids
        self.repair.action_repair_end()
        new_messages = self.repair.message_ids - messages
        self.assertTrue(new_messages)
        self.assertTrue(
            new_messages,
            "No message was posted on the repair order after ending repair",
        )
