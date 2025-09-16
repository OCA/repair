# Copyright 2025
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairFollowLotLocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "test partner"})
        stock_root = cls.env.ref("stock.stock_location_stock")
        cls.loc_a = cls.env["stock.location"].create(
            {"name": "A", "usage": "internal", "location_id": stock_root.id}
        )
        cls.loc_b = cls.env["stock.location"].create(
            {"name": "B", "usage": "internal", "location_id": stock_root.id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "product to repair", "type": "product", "tracking": "lot"}
        )
        cls.lot = cls.env["stock.lot"].create(
            {"name": "LOT-001", "product_id": cls.product.id}
        )

    @classmethod
    def _set_qty(cls, location, qty):
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, location, qty, lot_id=cls.lot
        )

    @classmethod
    def _move_lot(cls, src, dest, qty):
        move = cls.env["stock.move"].create(
            {
                "name": "internal move",
                "product_id": cls.product.id,
                "product_uom_qty": qty,
                "location_id": src.id,
                "location_dest_id": dest.id,
            }
        )
        move._action_confirm()
        move._action_assign()
        move_lines = move.move_line_ids
        move_lines.qty_done = qty
        move._action_done()
        return move

    def _create_repair(self, location):
        return self.env["repair.order"].create(
            {
                "name": "RMA-1",
                "partner_id": self.partner.id,
                "product_id": self.product.id,
                "product_qty": 1.0,
                "location_id": location.id,
                "lot_id": self.lot.id,
            }
        )

    def test_follow_location_change(self):
        self._set_qty(self.loc_a, 1.0)
        self.assertEqual(self.lot.quant_ids.location_id, self.loc_a)
        repair = self._create_repair(self.loc_a)
        repair.follow_lot_location = True
        self.assertEqual(repair.location_id, self.loc_a)
        move = self._move_lot(self.loc_a, self.loc_b, 1.0)
        self.assertEqual(move.state, "done")
        self.assertEqual(repair.location_id, self.loc_b)

    def test_no_follow_location_change(self):
        self._set_qty(self.loc_a, 1.0)
        self.assertEqual(self.lot.quant_ids.location_id, self.loc_a)
        repair = self._create_repair(self.loc_a)
        repair.follow_lot_location = False
        self.assertEqual(repair.location_id, self.loc_a)
        move = self._move_lot(self.loc_a, self.loc_b, 1.0)
        self.assertEqual(move.state, "done")
        self.assertEqual(repair.location_id, self.loc_a)
