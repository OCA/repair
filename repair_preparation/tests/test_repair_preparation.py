# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestRepairPreparation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "test partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "product to repair", "type": "product"}
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "product to consume", "type": "product", "tracking": "lot"}
        )
        cls.product_c_2 = cls.env["product.product"].create(
            {"name": "product to consume 2", "type": "product"}
        )
        cls.lot = cls.env["stock.lot"].create(
            {"name": "lot", "product_id": cls.product_c.id}
        )
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "WH", "code": "wh_test"}
        )
        cls.stock_loc = cls.warehouse.lot_stock_id

        cls.prep_loc = cls.env["stock.location"].create(
            {
                "name": "Preparation",
                "usage": "internal",
                "location_id": cls.stock_loc.id,
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.prep_type = cls.env["stock.picking.type"].create(
            {
                "name": "Preparation",
                "code": "internal",
                "warehouse_id": cls.warehouse.id,
                "sequence_code": "PREP",
                "default_location_src_id": cls.stock_loc.id,
                "default_location_dest_id": cls.prep_loc.id,
            }
        )
        cls.warehouse.write(
            {
                "repair_preparation_enabled": True,
                "repair_preparation_picking_type_id": cls.prep_type.id,
            }
        )
        cls.prep_route = cls.env["stock.route"].create(
            {
                "name": "Route to Preparation",
                "product_selectable": True,
                "warehouse_selectable": False,
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.prep_rule = cls.env["stock.rule"].create(
            {
                "name": "Pull to Preparation",
                "route_id": cls.prep_route.id,
                "action": "pull",
                "picking_type_id": cls.prep_type.id,
                "location_src_id": cls.stock_loc.id,
                "location_dest_id": cls.prep_loc.id,
                "warehouse_id": cls.warehouse.id,
            }
        )
        cls.product_c.write({"route_ids": [(4, cls.prep_route.id)]})
        cls.product_c_2.write({"route_ids": [(4, cls.prep_route.id)]})

        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.prep_loc, 1.0
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_c, cls.stock_loc, 10.0, lot_id=cls.lot
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_c_2, cls.stock_loc, 10.0
        )
        cls.repair = cls.env["repair.order"].create(
            {
                "partner_id": cls.partner.id,
                "product_id": cls.product.id,
                "location_id": cls.prep_loc.id,
                "priority": "1",
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.line = cls._create_repair_line(cls.product_c)

    @classmethod
    def _do_picking(cls, picking):
        for move in picking.move_ids:
            move.quantity_done = move.product_qty
        picking._action_done()

    @classmethod
    def _create_repair_line(cls, product):
        return cls.env["repair.line"].create(
            {
                "name": "replace product",
                "repair_id": cls.repair.id,
                "type": "add",
                "price_unit": 100,
                "product_id": product.id,
                "product_uom_qty": 2.0,
            }
        )

    @classmethod
    def _get_available_qty(cls, product, location):
        return cls.env["stock.quant"]._get_available_quantity(product, location)

    def test_validate_runs_procurement(self):
        self.repair.action_validate()
        self.assertEqual(self.repair.state, "confirmed")
        self.assertTrue(self.line.preparation_move_ids)
        self.assertTrue(self.repair.preparation_picking_ids)
        self.assertEqual(
            self.prep_type, self.repair.preparation_picking_ids.picking_type_id
        )
        move = self.line.preparation_move_ids
        self.assertEqual(move.product_id, self.product_c)
        self.assertEqual(move.location_id, self.stock_loc)
        self.assertEqual(move.location_dest_id, self.prep_loc)

    def test_create_new_line_under_repair_triggers_procurement(self):
        self.test_validate_runs_procurement()
        self.repair.action_repair_start()
        self.assertEqual(self.repair.state, "under_repair")
        new_line = self._create_repair_line(self.product_c_2)
        self.assertTrue(new_line.preparation_move_ids)
        self.assertEqual(
            len(self.repair.preparation_picking_ids), 1
        )  # the new move is added to the existing picking
        self.assertEqual(len(self.repair.operations.preparation_move_ids), 2)
        move = new_line.preparation_move_ids
        self.assertEqual(move.product_id, self.product_c_2)
        self.assertEqual(move.location_id, self.stock_loc)
        self.assertEqual(move.location_dest_id, self.prep_loc)

    def test_write_done_move_not_allowed(self):
        self.test_validate_runs_procurement()
        self._do_picking(self.repair.preparation_picking_ids)
        self.assertEqual(self.repair.preparation_picking_ids.state, "done")
        with self.assertRaisesRegex(
            ValidationError,
            "You cannot modify product/quantity for preparation lines "
            "because some linked moves are already done",
        ):
            self.line.write({"product_uom_qty": 3.0})

    def test_write_repair_line_cancels_and_reprocures(self):
        self.test_validate_runs_procurement()
        self.repair.action_repair_start()
        self.assertEqual(len(self.repair.preparation_picking_ids), 1)
        self.assertEqual(len(self.line.preparation_move_ids), 1)
        self.line.write({"product_uom_qty": 5.0})
        self.assertEqual(len(self.line.preparation_move_ids), 2)
        self.assertSetEqual(
            set(self.line.preparation_move_ids.mapped("state")), {"cancel", "assigned"}
        )
        self.assertEqual(len(self.repair.preparation_picking_ids), 2)
        self.assertSetEqual(
            set(self.repair.preparation_picking_ids.mapped("state")),
            {"cancel", "assigned"},
        )

    def test_action_repair_end_checks(self):

        with self.assertRaisesRegex(
            ValidationError,
            "Preparation picking not found. Please procure/prepare parts first",
        ):
            self.repair.action_repair_end()
        self.repair.action_validate()
        self.repair.action_repair_start()
        with self.assertRaisesRegex(
            ValidationError, "Preparation picking is not done yet"
        ):
            self.repair.action_repair_end()
        self.assertEqual(self._get_available_qty(self.product_c, self.prep_loc), 0)
        self._do_picking(self.repair.preparation_picking_ids)
        self.assertEqual(self._get_available_qty(self.product_c, self.prep_loc), 2)
        self.repair.action_repair_end()
        self.repair.action_repair_done()
        self.assertEqual(self.repair.state, "done")
        self.repair.action_repair_done()
        self.assertEqual(self.line.move_id.state, "done")
        self.assertEqual(self._get_available_qty(self.product_c, self.prep_loc), 0)

    def test_preparation_disabled(self):
        """default behavior, the products are consumed without a preparation picking"""
        self.warehouse.repair_preparation_enabled = False
        self.repair.action_validate()
        self.assertFalse(self.repair.preparation_picking_ids)
        self.repair.action_repair_start()
        self.assertFalse(self.line.preparation_move_ids)

    def test_update_repair_line_after_preparation(self):
        self.test_validate_runs_procurement()
        self.line.location_id = self.stock_loc
        self.assertFalse(self.line.lot_id)
        move_line = self.repair.preparation_picking_ids.move_line_ids
        self.assertEqual(move_line.lot_id, self.lot)
        self._do_picking(self.repair.preparation_picking_ids)
        self.assertEqual(self.line.location_id, self.prep_loc)
        self.assertEqual(self.line.lot_id, self.lot)
