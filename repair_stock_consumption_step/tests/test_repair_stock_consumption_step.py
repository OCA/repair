# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import Common


class TestRepairStockConsumptionStep(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repair.action_validate()
        cls.repair.action_repair_ready()
        cls.repair.action_repair_start()

    def test_repair_done_no_consumption_step(self):
        self.warehouse.repair_consumption_step = False
        self.repair.action_repair_end()
        moves = self.env["stock.move"].search([("repair_id", "=", self.repair.id)])
        self.assertTrue(moves)
        self.assertTrue(all(m.state == "done" for m in moves))
        self.assertFalse(self.repair.consumption_picking_id)

    def test_repair_done_with_consumption_step(self):
        self.repair.action_repair_end()
        self.assertEqual(self.repair.state, "consumption")
        self.assertTrue(self.repair.consumption_picking_id)
        moves = self.env["stock.move"].search([("repair_id", "=", self.repair.id)])
        pick = self.repair.consumption_picking_id
        self.assertEqual(self.repair.operations.lot_id, pick.move_line_ids.lot_id)
        self.assertTrue(moves)
        self.assertEqual(pick.move_ids, moves)
        self.assertEqual(
            pick.location_id,
            self.warehouse.repair_consumption_picking_type_id.default_location_src_id,
        )
        self.assertEqual(
            pick.location_dest_id,
            self.warehouse.repair_consumption_picking_type_id.default_location_dest_id,
        )
        self.assertSetEqual(set(moves.mapped("state")), {"assigned"})
        self.assertIn(pick.state, "assigned")
        self.assertEqual(pick.move_line_ids, moves.move_line_ids)
        self._do_picking(pick)
        self.assertEqual(self.repair.state, "done")

    def test_repair_done_with_consumption_step_invoice_after_repair(self):
        self.repair.invoice_method = "after_repair"
        self.repair.action_repair_end()
        self.assertEqual(self.repair.state, "consumption")
        self._do_picking(self.repair.consumption_picking_id)
        self.assertEqual(self.repair.state, "2binvoiced")
