# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    """Inherited Repair Order tracking model context."""

    _inherit = "repair.order"

    imei_number = fields.Char(
        string="IMEI Number",
        copy=False,
        index=True,
        help="15-digit IMEI number of the device being repaired.",
    )
    imei_required = fields.Boolean(
        compute="_compute_imei_required",
        store=False,
    )

    @api.model
    def _normalize_imei(self, imei):
        if not imei:
            return imei

        return re.sub(r"\D", "", imei)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("imei_number"):
                vals["imei_number"] = self._normalize_imei(vals["imei_number"])

        return super().create(vals_list)

    def write(self, vals):
        if vals.get("imei_number"):
            vals["imei_number"] = self._normalize_imei(vals["imei_number"])

        return super().write(vals)

    @api.depends(
        "product_id",
        "product_id.imei_required",
        "product_id.categ_id.imei_required",
    )
    def _compute_imei_required(self):
        for record in self:
            if not record.product_id:
                record.imei_required = False
                continue

            imei_settings = record.product_id.imei_required or "parent"

            if imei_settings == "parent" and record.product_id.categ_id:
                cat_required = record.product_id.categ_id.imei_required
                imei_settings = "yes" if cat_required else "no"

            record.imei_required = imei_settings == "yes"

    @api.model
    def _imei_luhn_is_valid(self, value):
        if not value or not isinstance(value, str):
            return False

        imei_clean = self._normalize_imei(value)
        if len(imei_clean) != 15 or not imei_clean.isdigit():
            return False

        digits = [int(digit) for digit in imei_clean]
        total = 0
        for idx, digit in enumerate(reversed(digits)):
            if idx % 2 == 1:
                doubled = digit * 2
                total += doubled - 9 if doubled > 9 else doubled
            else:
                total += digit

        return total % 10 == 0

    @api.onchange("imei_number")
    def _onchange_imei_number_warning(self):
        if not self.imei_number:
            return False

        imei_clean = self._normalize_imei(self.imei_number)
        if imei_clean and not self._imei_luhn_is_valid(imei_clean):
            return {
                "warning": {
                    "title": self.env._("Invalid IMEI Format"),
                    "message": self.env._(
                        "The entered IMEI %s does not pass "
                        "the standard Luhn checksum test.",
                        self.imei_number,
                    ),
                }
            }
        return False

    @api.constrains("imei_number", "product_id", "state")
    def _check_valid_imei(self):
        for record in self:
            raw_imei = record.imei_number or ""
            imei_clean = self._normalize_imei(raw_imei)

            if record.imei_required and not imei_clean:
                raise ValidationError(
                    self.env._("IMEI Number is required for this repair order.")
                )

            if imei_clean and not self._imei_luhn_is_valid(imei_clean):
                raise ValidationError(
                    self.env._(
                        "The IMEI number '%s' is invalid. "
                        "Please enter a valid 15-digit IMEI.",
                        record.imei_number,
                    )
                )

        records_to_check = self.filtered(
            lambda r: r.imei_number and r.state not in ("cancel", "done")
        )

        if not records_to_check:
            return

        domain = [
            ("imei_number", "in", records_to_check.mapped("imei_number")),
            ("state", "not in", ["cancel", "done"]),
        ]

        grouped_data = self.env["repair.order"].read_group(
            domain,
            ["imei_number", "id:count"],
            ["imei_number"],
        )

        for group in grouped_data:
            imei_val = group["imei_number"]
            if group["imei_number_count"] > 1:
                raise ValidationError(
                    self.env._(
                        "An active repair order already exists "
                        "for IMEI No %(imei)s.",
                        imei=imei_val,
                    )
                )
