# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    @api.onchange("lot_id")
    def _onchange_lot_id_set_product(self):
        """Allow selecting the repair product by lot/serial.

        When a lot/serial number is selected first, automatically set the
        corresponding product on the repair order. Unit of measure will be
        automatically set by Odoo's standard compute method.
        This lets users start the process by scanning a lot.
        """
        for order in self:
            if order.lot_id and order.lot_id.product_id:
                order.product_id = order.lot_id.product_id
            elif not order.lot_id:
                order.product_id = False
