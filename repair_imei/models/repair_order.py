# pylint: disable=abstract-method
"""Handle custom business logic for IMEI validation on repair orders."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    """Inherited Repair Order tracking model context."""

    _inherit = "repair.order"

    imei_no = fields.Char(
        string="IMEI No",
        copy=False,
        help="15-digit IMEI number of the device being repaired.",
    )
    imei_required = fields.Boolean(
        compute="_compute_imei_required",
        store=False,
    )

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

            imei_settings = (
                getattr(record.product_id, "imei_required", "parent") or "parent"
            )

            if imei_settings == "parent" and record.product_id.categ_id:
                cat_required = getattr(
                    record.product_id.categ_id, "imei_required", False
                )
                imei_settings = "yes" if cat_required else "no"

            record.imei_required = imei_settings == "yes"

    @staticmethod
    def _imei_luhn_is_valid(value):
        if not value or not isinstance(value, str):
            return False

        imei_clean = value.strip().replace(" ", "").replace("-", "")
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

    @api.onchange("imei_no")
    def _onchange_imei_no_warning(self):
        if not self.imei_no:
            return False

        imei_clean = self.imei_no.strip().replace(" ", "").replace("-", "")
        if imei_clean and not self._imei_luhn_is_valid(imei_clean):
            return {
                "warning": {
                    "title": self.env._("Invalid IMEI Format"),
                    "message": self.env._(
                        "The entered IMEI %s does not pass "
                        "the standard Luhn checksum test.",
                        self.imei_no,
                    ),
                }
            }
        return False

    @api.constrains("imei_no", "product_id", "state")
    def _check_valid_imei(self):
        for record in self:
            raw_imei = record.imei_no or ""
            imei_clean = raw_imei.strip().replace(" ", "").replace("-", "")

            if record.imei_required and not imei_clean:
                raise ValidationError(
                    self.env._("IMEI Number is required for this repair order.")
                )

            if imei_clean and not self._imei_luhn_is_valid(imei_clean):
                raise ValidationError(
                    self.env._(
                        """The IMEI number '%s' is invalid.
                    Please enter a valid 15-digit IMEI.""",
                        record.imei_no,
                    )
                )

            if imei_clean:
                duplicate = self.search(
                    [
                        ("id", "!=", record.id),
                        ("imei_no", "=", imei_clean),
                        ("state", "not in", ["cancel", "done"]),
                    ],
                    limit=1,
                )
                if duplicate:
                    raise ValidationError(
                        self.env._(
                            "An active repair order (%(order_name)s) already "
                            "exists for IMEI No %(imei)s.",
                            order_name=duplicate.name,
                            imei=imei_clean,
                        )
                    )
