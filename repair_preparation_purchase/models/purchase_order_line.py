# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    repair_line_id = fields.Many2one(
        comodel_name="repair.line", ondelete="cascade", readonly=True
    )

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        po_line_vals = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        po_line_vals["repair_line_id"] = values.get("repair_line_id")
        return po_line_vals
