from odoo.tests.common import TransactionCase


class TestPartnerRepairButton(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Repair Partner"})
        self.repair_order = self.env["repair.order"].create(
            {
                "name": "Test Repair",
                "partner_id": self.partner.id,
            }
        )

    def test_repair_count(self):
        self.partner._compute_repair_count()
        self.assertEqual(self.partner.repair_count, 1)

    def test_action_view_repairs(self):
        action = self.partner.action_view_repairs()
        self.assertEqual(action["res_model"], "repair.order")
        self.assertIn(("partner_id", "=", self.partner.id), action["domain"])
