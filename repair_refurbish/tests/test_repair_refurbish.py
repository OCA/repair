# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestMrpMtoWithStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repair_obj = cls.env["repair.order"]
        cls.product_obj = cls.env["product.product"]
        cls.move_obj = cls.env["stock.move"]

        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location_stock = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.refurbish_loc = cls.env.ref("repair_refurbish.stock_location_refurbish")

        cls.refurbish_product = cls.product_obj.create(
            {"name": "Refurbished Awesome Screen", "type": "product"}
        )
        cls.product = cls.product_obj.create(
            {
                "name": "Awesome Screen",
                "type": "product",
                "refurbish_product_id": cls.refurbish_product.id,
            }
        )
        cls.material = cls.product_obj.create({"name": "Materials", "type": "consu"})
        cls.material2 = cls.product_obj.create({"name": "Materials", "type": "product"})
        cls._update_product_qty(cls, cls.product, cls.stock_location_stock, 10.0)
        cls._update_product_qty(cls, cls.material2, cls.stock_location_stock, 10.0)

    def _update_product_qty(self, product, location, quantity, lot=None):
        self.env["stock.quant"].create(
            {
                "location_id": location.id,
                "product_id": product.id,
                "inventory_quantity": quantity,
                "lot_id": lot and lot.id,
            }
        ).action_apply_inventory()
        return quantity

    def test_01_repair_refurbish(self):
        """Tests that locations are properly set with a product to
        refurbish, then complete repair."""
        repair = self.repair_obj.create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "picking_type_id": self.warehouse.repair_type_id.id,
            }
        )
        self.assertFalse(repair.to_refurbish)
        repair.to_refurbish = True
        repair._onchange_to_refurbish()
        self.assertEqual(repair.location_id, self.stock_location_stock)
        self.assertEqual(repair.refurbish_location_dest_id, self.stock_location_stock)

        # Complete repair:
        repair.action_validate()
        repair.action_repair_start()
        repair.action_repair_end()
        moves = self.move_obj.search([("repair_id", "=", repair.id)])
        self.assertEqual(len(moves), 2)
        for m in moves:
            self.assertEqual(m.state, "done")
            if m.product_id == self.product:
                self.assertEqual(m.location_id, self.stock_location_stock)
                self.assertEqual(m.location_dest_id, self.refurbish_loc)
                self.assertEqual(
                    m.mapped("move_line_ids.location_id"), self.stock_location_stock
                )
                self.assertEqual(
                    m.mapped("move_line_ids.location_dest_id"), self.refurbish_loc
                )
            elif m.product_id == self.refurbish_product:
                self.assertEqual(m.location_id, self.refurbish_loc)
                self.assertEqual(m.location_dest_id, self.stock_location_stock)
                self.assertEqual(
                    m.mapped("move_line_ids.location_id"), self.refurbish_loc
                )
                self.assertEqual(
                    m.mapped("move_line_ids.location_dest_id"),
                    self.stock_location_stock,
                )
            else:
                self.assertTrue(False, "Unexpected move.")
        self.assertEqual(
            repair.refurbish_move_id.move_line_ids.consume_line_ids,
            repair.move_id.move_line_ids,
        )
        self.assertEqual(
            repair.move_id.move_line_ids.produce_line_ids,
            repair.refurbish_move_id.move_line_ids,
        )

    def test_02_repair_no_refurbish(self):
        """Tests normal repairs does not fail and normal location for consumed
        material"""
        repair = self.repair_obj.create(
            {
                "product_id": self.product.id,
                "product_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "picking_type_id": self.warehouse.repair_type_id.id,
                "to_refurbish": False,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.material2.id,
                            "product_uom_qty": 1.0,
                            "state": "draft",
                            "repair_line_type": "add",
                            "location_id": self.stock_location_stock.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )

        # Complete repair:
        repair.action_validate()
        repair.action_repair_start()
        # Component
        move = self.move_obj.search(
            [("product_id", "=", self.material2.id), ("repair_id", "=", repair.id)],
        )
        self.assertEqual(len(move), 1)
        self.assertEqual(move.location_dest_id, repair.location_dest_id)
        move.move_line_ids.picked = True
        # Repaired product:
        res = repair.action_repair_end()
        self.assertFalse(isinstance(res, dict), "action_repair_end has failed")
        repaired_move = self.move_obj.search(
            [("product_id", "=", self.product.id), ("repair_id", "=", repair.id)],
        )
        self.assertEqual(len(repaired_move), 1)
        self.assertEqual(repaired_move.location_id, self.stock_location_stock)
        self.assertEqual(repaired_move.location_dest_id, self.stock_location_stock)

    def test_03_repair_refurbish_traceability(self):
        """Tests that the refurbished product is traceable back to the
        initial product, which keeps its own history, and to the parts
        added during the repair, like a manufacturing order does."""
        refurbish_product = self.product_obj.create(
            {
                "name": "Refurbished Tracked Screen",
                "type": "product",
                "tracking": "serial",
            }
        )
        product = self.product_obj.create(
            {
                "name": "Tracked Screen",
                "type": "product",
                "tracking": "serial",
                "refurbish_product_id": refurbish_product.id,
            }
        )
        lot = self.env["stock.lot"].create(
            {
                "name": "SN-OLD",
                "product_id": product.id,
                "company_id": self.env.company.id,
            }
        )
        refurbish_lot = self.env["stock.lot"].create(
            {
                "name": "SN-NEW",
                "product_id": refurbish_product.id,
                "company_id": self.env.company.id,
            }
        )
        self._update_product_qty(product, self.stock_location_stock, 1.0, lot=lot)
        shelf = self.env.ref("stock.stock_location_components")
        internal_move = self.move_obj.create(
            {
                "name": "Move to shelf",
                "product_id": product.id,
                "product_uom_qty": 1.0,
                "product_uom": product.uom_id.id,
                "location_id": self.stock_location_stock.id,
                "location_dest_id": shelf.id,
                "move_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "lot_id": lot.id,
                            "quantity": 1.0,
                            "product_uom_id": product.uom_id.id,
                            "location_id": self.stock_location_stock.id,
                            "location_dest_id": shelf.id,
                        },
                    )
                ],
            }
        )
        internal_move._action_confirm()
        internal_move.picked = True
        internal_move._action_done()
        history_lines = self.env["stock.move.line"].search(
            [("lot_id", "=", lot.id), ("state", "=", "done")]
        )
        self.assertEqual(len(history_lines), 2)
        self._update_product_qty(self.material2, shelf, 1.0)
        repair = self.repair_obj.create(
            {
                "product_id": product.id,
                "lot_id": lot.id,
                "product_qty": 1.0,
                "product_uom": product.uom_id.id,
                "picking_type_id": self.warehouse.repair_type_id.id,
                "location_id": shelf.id,
                "to_refurbish": True,
                "refurbish_product_id": refurbish_product.id,
                "refurbish_lot_id": refurbish_lot.id,
                "refurbish_location_dest_id": shelf.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.material2.id,
                            "product_uom_qty": 1.0,
                            "state": "draft",
                            "repair_line_type": "add",
                            "location_id": self.stock_location_stock.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )
        res = repair.action_validate()
        self.assertEqual(repair.state, "confirmed", res)
        repair.action_repair_start()
        repair.move_ids.move_line_ids.picked = True
        res = repair.action_repair_end()
        self.assertEqual(repair.state, "done", res)
        part_lines = repair.move_ids.move_line_ids
        original_lines = repair.move_id.move_line_ids
        refurbished_lines = repair.refurbish_move_id.move_line_ids
        self.assertEqual(len(original_lines), 1)
        self.assertEqual(len(part_lines), 1)
        self.assertEqual(
            refurbished_lines.consume_line_ids, original_lines | part_lines
        )
        self.assertFalse(original_lines.consume_line_ids)
        self.assertEqual(original_lines.produce_line_ids, refurbished_lines)
        self.assertEqual(part_lines.produce_line_ids, refurbished_lines)
        report = self.env["stock.traceability.report"]
        lines = report._lines(
            line_id=refurbished_lines.id,
            model_id=refurbished_lines.id,
            model="stock.move.line",
        )
        self.assertEqual(
            {line["model_id"] for line in lines}, set((original_lines | part_lines).ids)
        )
        original_report_line = [
            line for line in lines if line["model_id"] == original_lines.id
        ][0]
        self.assertEqual(original_report_line["reference_id"], repair.name)
        self.assertTrue(original_report_line["unfoldable"])
        lines = report._lines(
            line_id=original_lines.id,
            model_id=original_lines.id,
            model="stock.move.line",
        )
        self.assertEqual(
            [line["model_id"] for line in lines], internal_move.move_line_ids.ids
        )
