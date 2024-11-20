# Copyright (C) 2021 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import TransactionCase


class TestRepairType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type = cls.env.ref("repair.picking_type_warehouse0_repair")
        cls.product_4 = cls.env.ref("product.product_product_4")
        cls.product_3 = cls.env.ref("product.product_product_3")
        cls.product_11 = cls.env.ref("product.product_product_11")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

    def _create_repair_order(
        self,
        picking_type_ref,
        product_ref,
        repair_line_type,
        product_qty,
        component_ref,
    ):
        """Helper method to create a repair order."""
        return self.env["repair.order"].create(
            {
                "picking_type_id": picking_type_ref.id,
                "product_id": product_ref.id,
                "product_uom": self.uom_unit.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": f"{repair_line_type.capitalize()} Component",
                            "repair_line_type": repair_line_type,
                            "product_id": component_ref.id,
                            "product_uom_qty": product_qty,
                        },
                    )
                ],
            }
        )

    def _set_default_location(self, location_field, location_ref):
        """Helper method to set default locations."""
        self.picking_type[location_field] = location_ref

    def _test_repair_location(
        self, repair_line_type, location_field, location_ref, component_ref, product_qty
    ):
        """Reusable test logic for validating repair locations."""
        self._set_default_location(location_field, location_ref)
        repair = self._create_repair_order(
            self.picking_type,
            self.product_4,
            repair_line_type,
            product_qty,
            component_ref,
        )
        repair._action_repair_confirm()
        self.assertEqual(
            repair.move_ids.move_line_ids.location_id,
            location_ref,
        )

    def test_get_repair_locations_remove(self):
        self._test_repair_location(
            repair_line_type="remove",
            location_field="default_remove_location_src_id",
            location_ref=self.customer_location,
            component_ref=self.product_3,
            product_qty=3,
        )

    def test_get_repair_locations_recycle(self):
        self._test_repair_location(
            repair_line_type="recycle",
            location_field="default_recycle_location_src_id",
            location_ref=self.customer_location,
            component_ref=self.product_11,
            product_qty=3,
        )

    def test_get_repair_locations_add(self):
        self._test_repair_location(
            repair_line_type="add",
            location_field="default_add_location_src_id",
            location_ref=self.customer_location,
            component_ref=self.product_3,
            product_qty=5,
        )
