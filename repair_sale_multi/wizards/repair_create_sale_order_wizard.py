# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.exceptions import UserError


class RepairCreateSaleOrderWizard(models.TransientModel):
    _name = "repair.create.sale.order.wizard"
    _description = "Create Quotation from Repair Orders"

    repair_order_ids = fields.Many2many("repair.order", required=True)

    def action_create_sale_order(self):
        self.ensure_one()
        repairs = self.repair_order_ids
        partner_ids = repairs.mapped("partner_id")
        if len(partner_ids) > 1:
            raise UserError(
                self.env._("All repair orders must belong to the same customer.")
            )
        result = repairs.action_create_sale_order()
        return result
