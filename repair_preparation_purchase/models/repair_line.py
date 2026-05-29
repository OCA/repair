# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class RepairLine(models.Model):

    _inherit = "repair.line"

    def write(self, vals):

        fields_affecting = {"type", "product_id", "product_uom_qty", "product_uom"}
        if all(_field not in vals for _field in fields_affecting):
            return super().write(vals)

        # The super call from "repair_preparation" will re-trigger the procurement
        # -> we cancel existing PO's before the procurement is run to ensure
        # no more qty than expected on the PO
        orders_under_repair = self.repair_id.filtered(
            lambda ro: ro.state == "under_repair"
        )
        if blocking_pos := orders_under_repair.preparation_purchase_ids.filtered(
            lambda m: m.state not in ("draft", "cancel")
        ):
            raise ValidationError(
                _(
                    "You cannot modify product/quantity for preparation lines "
                    "because some linked purchase orders are already confirmed.\n"
                    "Blocking purchase orders: %(purchase_orders)s",
                    purchase_orders=", ".join(blocking_pos.mapped("name")),
                )
            )
        if draft_pos := orders_under_repair.preparation_purchase_ids.filtered(
            lambda po: po.state == "draft"
        ):
            draft_pos.button_cancel()
        return super().write(vals)
