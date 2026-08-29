# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# pylint: disable=unsubscriptable-object
"""Test suite for IMEI validation and tracking logic in repair orders."""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestRepairIMEI(TransactionCase):
    """Test suite for IMEI validation and tracking logic in repair orders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.valid_imei = "490154203237518"
        cls.invalid_imei = "490154203237519"

        cls.category_imei_required = cls.env["product.category"].create(
            {
                "name": "Mobile Phones (IMEI Mandatory)",
                "imei_required": True,
            }
        )

        cls.category_imei_optional = cls.env["product.category"].create(
            {
                "name": "Accessories (IMEI Optional)",
                "imei_required": False,
            }
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
            }
        )

        cls.product_parent_required = cls.env["product.product"].create(
            {
                "name": "Phone Parent Required",
                "categ_id": cls.category_imei_required.id,
                "imei_required": "parent",
            }
        )

        cls.product_parent_optional = cls.env["product.product"].create(
            {
                "name": "Accessory Parent Optional",
                "categ_id": cls.category_imei_optional.id,
                "imei_required": "parent",
            }
        )

        cls.product_explicit_yes = cls.env["product.product"].create(
            {
                "name": "Accessory Forced IMEI",
                "categ_id": cls.category_imei_optional.id,
                "imei_required": "yes",
            }
        )

        cls.product_explicit_no = cls.env["product.product"].create(
            {
                "name": "Phone Exempt IMEI",
                "categ_id": cls.category_imei_required.id,
                "imei_required": "no",
            }
        )

    def test_01_luhn_checksum_validation(self):
        """Test the static Luhn algorithm implementation."""
        repair_model = self.env["repair.order"]
        # pylint: disable=protected-access
        self.assertTrue(repair_model._imei_luhn_is_valid(self.valid_imei))
        self.assertFalse(repair_model._imei_luhn_is_valid(self.invalid_imei))
        self.assertFalse(repair_model._imei_luhn_is_valid("12345"))
        self.assertFalse(repair_model._imei_luhn_is_valid("ABCD54203237518"))
        self.assertFalse(repair_model._imei_luhn_is_valid(None))
        self.assertFalse(repair_model._imei_luhn_is_valid(123456789012345))

    def test_02_parent_category_fallback_required(self):
        """Test 'parent' mode when category imei_required is True."""
        # Provide valid IMEI on creation so record creation succeeds
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_required.id,
                "imei_no": self.valid_imei,
            }
        )
        self.assertTrue(repair.imei_required)

        # Confirm validation fails when IMEI is stripped
        with self.assertRaises(ValidationError):
            repair.write({"imei_no": False})

    def test_03_parent_category_fallback_optional(self):
        """Test 'parent' mode when category imei_required is False."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_optional.id,
                "imei_no": False,
            }
        )
        self.assertFalse(repair.imei_required)

    def test_04_explicit_yes_override(self):
        """Test template explicit 'yes' overrides category imei_required=False."""
        # Provide valid IMEI on creation so record creation succeeds
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_explicit_yes.id,
                "imei_no": self.valid_imei,
            }
        )
        self.assertTrue(repair.imei_required)

        # Creating without IMEI must raise ValidationError
        with self.assertRaises(ValidationError):
            self.env["repair.order"].create(
                {
                    "partner_id": self.partner.id,
                    "product_id": self.product_explicit_yes.id,
                    "imei_no": False,
                }
            )

    def test_05_explicit_no_override(self):
        """Test template explicit 'no' overrides category imei_required=True."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_explicit_no.id,
                "imei_no": False,
            }
        )
        self.assertFalse(repair.imei_required)

    def test_06_onchange_imei_no_warning(self):
        """Test UI onchange warning dictionary returns for invalid IMEI."""
        repair = self.env["repair.order"].new(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_optional.id,
            }
        )
        # 1. Empty imei returns False
        repair.imei_no = False
        self.assertFalse(repair._onchange_imei_no_warning())

        # 2. Valid imei returns False
        repair.imei_no = self.valid_imei
        self.assertFalse(repair._onchange_imei_no_warning())

        # 3. Invalid imei returns warning dict
        repair.imei_no = self.invalid_imei
        res_warning = repair._onchange_imei_no_warning()
        self.assertIn("warning", res_warning)

    def test_07_no_product_set_imei_required_false(self):
        """Test compute edge case when product_id is not set."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": False,
                "imei_no": False,
            }
        )
        self.assertFalse(repair.imei_required)

    def test_08_duplicate_imei_raises_validation_error(self):
        """Test that creating a second active repair order
        with the same IMEI raises ValidationError."""
        self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_explicit_yes.id,
                "imei_no": self.valid_imei,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["repair.order"].create(
                {
                    "partner_id": self.partner.id,
                    "product_id": self.product_explicit_yes.id,
                    "imei_no": self.valid_imei,
                }
            )

    def test_09_invalid_imei_raises_validation_error(self):
        """Test that writing an invalid Luhn checksum
        IMEI raises ValidationError on constraint."""
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_optional.id,
                "imei_no": False,
            }
        )
        with self.assertRaises(ValidationError):
            repair.write({"imei_no": self.invalid_imei})
