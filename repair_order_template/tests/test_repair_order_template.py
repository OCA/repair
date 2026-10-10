# Copyright 2024 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import Form, TransactionCase
from odoo.tools import html2plaintext

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestRepairOrderTemplate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.RepairOrderTemplate = cls.env["repair.order.template"]
        cls.ProductProduct = cls.env["product.product"]
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.product_1, cls.product_2 = cls.ProductProduct.create(
            [{"name": "MY-PRODUCT-1"}, {"name": "MY-PRODUCT-2"}]
        )
        cls.template = cls.RepairOrderTemplate.create(
            {
                "name": "General Repair",
                "line_ids": [
                    Command.create(
                        {
                            "type": "add",
                            "product_id": cls.product_1.id,
                            "product_uom": cls.product_1.uom_id.id,
                        }
                    ),
                    Command.create(
                        {
                            "type": "add",
                            "product_id": cls.product_2.id,
                            "product_uom": cls.product_2.uom_id.id,
                        }
                    ),
                ],
            }
        )
        cls.order = cls.env["repair.order"].create({})

    def test_repair_order_template_fill_lines(self):
        with Form(self.order) as order:
            order.repair_order_template_id = self.template
        self.assertEqual(len(self.order.repair_order_template_id.line_ids), 2)
        for move, line in zip(
            self.order.move_ids,
            self.order.repair_order_template_id.line_ids,
            strict=True,
        ):
            self.assertEqual(move.repair_line_type, line.type)
            self.assertEqual(move.product_id, line.product_id)
            self.assertEqual(move.product_uom, line.product_uom)
            self.assertAlmostEqual(move.product_uom_qty, line.product_uom_qty)

    def test_repair_order_template_fill_simple_fields(self):
        self.template.internal_notes = "Template notes"
        self.template.under_warranty = True
        with Form(self.order) as order:
            order.repair_order_template_id = self.template
        self.assertEqual(html2plaintext(self.order.internal_notes), "Template notes")
        self.assertEqual(self.order.under_warranty, True)

    def test_repair_order_template_does_not_overwrite_unset_fields(self):
        self.order.internal_notes = "test"
        with Form(self.order) as order:
            order.repair_order_template_id = self.template
        self.assertEqual(html2plaintext(self.order.internal_notes), "test")

    def test_repair_order_template_readonly(self):
        self.order.action_validate()
        with self.assertRaisesRegex(
            ValidationError, "Order Template can only be set on draft orders"
        ):
            self.order.repair_order_template_id = self.template
