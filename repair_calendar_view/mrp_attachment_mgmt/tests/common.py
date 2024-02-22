# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import fields
from odoo.tests import Form, common


class TestMrpAttachmentMgmtBase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.component_a = cls.env["product.product"].create(
            {
                "name": "Test Component A",
                "type": "product",
            }
        )
        cls.component_b = cls.env["product.product"].create(
            {
                "name": "Test Component B",
                "type": "product",
            }
        )
        cls.component_c = cls.env["product.product"].create(
            {
                "name": "Test Component C",
                "type": "product",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )
        cls.workcenter = cls.env["mrp.workcenter"].create(
            {
                "name": "Test workcenter",
                "resource_calendar_id": cls.env.ref(
                    "resource.resource_calendar_std"
                ).id,
            }
        )
        cls.bom = cls._create_mrp_bom(
            cls,
            cls.product,
            [(cls.component_a, 1), (cls.component_b, 1), (cls.component_c, 1)],
        )
        cls.mrp_production = cls._create_mrp_production(
            cls, [(cls.component_a, 1), (cls.component_b, 1), (cls.component_c, 1)]
        )
        cls.workorder = fields.first(cls.mrp_production.workorder_ids)
        cls.attachment_model = cls.env["ir.attachment"]

    def _create_mrp_production(self, components):
        mrp_production_form = Form(self.env["mrp.production"])
        mrp_production_form.product_id = self.product
        mrp_production_form.bom_id = self.bom
        for component in components:
            with mrp_production_form.move_raw_ids.new() as move_form:
                move_form.product_id = component[0]
                move_form.product_uom_qty = component[1]
        mrp_production = mrp_production_form.save()
        mrp_production.action_confirm()
        return mrp_production

    def _create_mrp_bom(self, product, components):
        mrp_bom_form = Form(self.env["mrp.bom"])
        mrp_bom_form.product_tmpl_id = product.product_tmpl_id
        bom_with_attachments = mrp_bom_form.save()
        self.env.user.groups_id += self.env.ref("mrp.group_mrp_routings")
        with Form(bom_with_attachments) as bom:
            for component in components:
                with bom.bom_line_ids.new() as line_form:
                    line_form.product_id = component[0]
                    line_form.product_qty = component[1]
            with bom.operation_ids.new() as operation_form:
                operation_form.name = "Operation 1"
                operation_form.workcenter_id = self.workcenter
                operation_form.bom_id = bom_with_attachments
        return bom_with_attachments

    def _create_attachment(self, product, name=False):
        name = name if name else "Test file %s" % product.name
        return self.attachment_model.create(
            {
                "name": name,
                "res_model": product._name,
                "res_id": product.id,
                "datas": base64.b64encode(b"\xff data"),
            }
        )
