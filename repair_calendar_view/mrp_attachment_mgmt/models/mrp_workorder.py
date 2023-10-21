# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def action_see_workorder_attachments(self):
        error = []
        for product in self.mapped("product_id"):
            if (
                product.message_attachment_count == 0
                and product.product_tmpl_id.message_attachment_count == 0
            ):
                error.append(product.display_name)
        if error:
            raise UserError(
                _("%d Product(s) without drawing:\n%s") % (len(error), "\n".join(error))
            )
        return self.product_id._action_show_attachments()
