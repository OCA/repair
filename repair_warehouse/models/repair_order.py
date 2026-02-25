# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):

    _inherit = "repair.order"

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        compute="_compute_warehouse_id",
        store=True,
        readonly=True,
        help="Warehouse inferred from the repair location. You can override it manually, "
        "but it must remain consistent with the selected location.",
        states={"draft": [("readonly", False)]},
    )
    location_id = fields.Many2one(
        domain="[('warehouse_id', '=', warehouse_id)]",
    )

    @api.depends("location_id")
    def _compute_warehouse_id(self):
        for rec in self:
            if rec.location_id.warehouse_id:
                rec.warehouse_id = rec.location_id.warehouse_id

    @api.constrains("location_id", "warehouse_id")
    def _check_warehouse_id(self):
        for rec in self:
            if (
                not rec.location_id
                or not rec.warehouse_id
                or rec.location_id.usage == "customer"
            ):
                continue
            loc_wh = rec.location_id.warehouse_id
            if loc_wh != rec.warehouse_id:
                raise ValidationError(
                    _(
                        "Warehouse mismatch:\n"
                        "- Repair location: %(loc)s (warehouse: %(loc_wh)s)\n"
                        "- Repair order warehouse: %(order_wh)s\n\n"
                        "Please select a location belonging to the same warehouse, "
                        "or change the warehouse to match the location.",
                        loc=rec.location_id.display_name,
                        loc_wh=loc_wh.display_name,
                        order_wh=rec.warehouse_id.display_name,
                    )
                )
