# Copyright 2026 Coder4web
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
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
        repair_model = self.env["repair.order"]

        self.assertTrue(repair_model._imei_luhn_is_valid(self.valid_imei))
        self.assertFalse(repair_model._imei_luhn_is_valid(self.invalid_imei))
        self.assertFalse(repair_model._imei_luhn_is_valid("12345"))
        self.assertFalse(repair_model._imei_luhn_is_valid("ABCD54203237518"))
        self.assertFalse(repair_model._imei_luhn_is_valid(None))
        self.assertFalse(repair_model._imei_luhn_is_valid(123456789012345))

    def test_02_parent_category_fallback_required(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_required.id,
                "imei_number": self.valid_imei,
            }
        )
        self.assertTrue(repair.imei_required)

        with self.assertRaises(ValidationError):
            repair.write({"imei_number": False})

    def test_03_parent_category_fallback_optional(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_optional.id,
                "imei_number": False,
            }
        )
        self.assertFalse(repair.imei_required)

    def test_04_explicit_yes_override(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_explicit_yes.id,
                "imei_number": self.valid_imei,
            }
        )
        self.assertTrue(repair.imei_required)

        with self.assertRaises(ValidationError):
            self.env["repair.order"].create(
                {
                    "partner_id": self.partner.id,
                    "product_id": self.product_explicit_yes.id,
                    "imei_number": False,
                }
            )

    def test_05_explicit_no_override(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_explicit_no.id,
                "imei_number": False,
            }
        )
        self.assertFalse(repair.imei_required)

    def test_06_onchange_imei_number_warning(self):
        repair = self.env["repair.order"].new(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_optional.id,
            }
        )
        repair.imei_number = False
        self.assertFalse(repair._onchange_imei_number_warning())

        repair.imei_number = self.valid_imei
        self.assertFalse(repair._onchange_imei_number_warning())

        repair.imei_number = self.invalid_imei
        res_warning = repair._onchange_imei_number_warning()
        self.assertIn("warning", res_warning)

    def test_07_no_product_set_imei_required_false(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": False,
                "imei_number": False,
            }
        )
        self.assertFalse(repair.imei_required)

    def test_08_duplicate_imei_raises_validation_error(self):
        self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_explicit_yes.id,
                "imei_number": self.valid_imei,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["repair.order"].create(
                {
                    "partner_id": self.partner.id,
                    "product_id": self.product_explicit_yes.id,
                    "imei_number": self.valid_imei,
                }
            )

    def test_09_invalid_imei_raises_validation_error(self):
        repair = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_parent_optional.id,
                "imei_number": False,
            }
        )
        with self.assertRaises(ValidationError):
            repair.write({"imei_number": self.invalid_imei})

    def test_10_batch_create_duplicate_imei(self):
        with self.assertRaises(ValidationError):
            self.env["repair.order"].create(
                [
                    {
                        "partner_id": self.partner.id,
                        "product_id": self.product_explicit_yes.id,
                        "imei_number": self.valid_imei,
                    },
                    {
                        "partner_id": self.partner.id,
                        "product_id": self.product_explicit_yes.id,
                        "imei_number": self.valid_imei,
                    },
                ]
            )

    def test_11_imei_normalization_with_formatting(self):
        repair1 = self.env["repair.order"].create(
            {
                "partner_id": self.partner.id,
                "product_id": self.product_explicit_yes.id,
                "imei_number": "490154-2032-37518",
            }
        )
        self.assertEqual(repair1.imei_number, self.valid_imei)

        with self.assertRaises(ValidationError):
            self.env["repair.order"].create(
                {
                    "partner_id": self.partner.id,
                    "product_id": self.product_explicit_yes.id,
                    "imei_number": "490154203237518",
                }
            )
