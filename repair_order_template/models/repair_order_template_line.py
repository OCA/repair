# Copyright 2024 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairOrderTemplateLine(models.Model):
    _name = "repair.order.template.line"
    _description = "Repair Order Template Line"
    _check_company_auto = True

    template_id = fields.Many2one(
        "repair.order.template",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        related="template_id.company_id",
        store=True,
    )
    type = fields.Selection(
        selection=lambda self: (
            self.env["stock.move"]
            ._fields["repair_line_type"]
            ._description_selection(self.env)
        ),
        required=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain="""
            [
                ('type', 'in', ['product', 'consu']),
                ('company_id', 'in', [False, company_id])
            ]
        """,
        check_company=True,
        required=True,
    )
    product_uom_category_id = fields.Many2one(
        related="product_id.uom_id.category_id",
    )
    product_uom = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        domain="[('category_id', '=', product_uom_category_id)]",
        compute="_compute_product_uom",
        readonly=False,
        required=True,
        store=True,
    )
    product_uom_qty = fields.Float(
        "Quantity",
        digits="Product Unit of Measure",
        required=True,
        default=1.0,
    )

    @api.depends("product_id")
    def _compute_product_uom(self):
        for rec in self:
            rec.product_uom = rec.product_id.uom_id

    def _prepare_move_values(self):
        return {
            "repair_line_type": self.type,
            "product_id": self.product_id.id,
            "product_uom": self.product_uom.id,
            "product_uom_qty": self.product_uom_qty,
        }
