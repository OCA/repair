# Copyright 2025 Vicent Cubells - Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import Form, TransactionCase


class TestRepariCommentsTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )
        self.base_comment_model = self.env["base.comment.template"]
        self.repair_before_comment = self._create_comment(
            "repair.order", "before_lines"
        )
        self.repair_after_comment = self._create_comment("repair.order", "after_lines")

        self.partner = self.env["res.partner"].create({"name": "Partner Test"})
        self.partner.base_comment_template_ids = [
            (4, self.repair_before_comment.id),
            (4, self.repair_after_comment.id),
        ]
        self.product = self.env["product.product"].create(
            {
                "name": "Test product",
            }
        )
        self.service = self.env["product.product"].create(
            {
                "name": "Test service",
                "type": "service",
                "list_price": 10,
            }
        )
        self.repair_order = self._create_repair_order()

    def _create_repair_order(self):
        repair_form = Form(self.env["repair.order"])
        repair_form.partner_id = self.partner
        repair_form.product_id = self.product
        with repair_form.operations.new() as line_form:
            line_form.product_id = self.service
        return repair_form.save()

    def _create_comment(self, models, position):
        return self.base_comment_model.create(
            {
                "name": "Comment " + position,
                "company_id": self.company.id,
                "position": position,
                "text": "Text " + position,
                "models": models,
            }
        )

    def test_comments_in_repair_order_report(self):
        res = self.env["ir.actions.report"]._render_qweb_html(
            "repair.action_report_repair_order", self.repair_order.ids
        )
        self.assertRegex(str(res[0]), self.repair_before_comment.text)
        self.assertRegex(str(res[0]), self.repair_after_comment.text)

    def test_comments_in_repair_order(self):
        self.assertTrue(
            self.repair_after_comment in self.repair_order.comment_template_ids
        )
        self.assertTrue(
            self.repair_before_comment in self.repair_order.comment_template_ids
        )
