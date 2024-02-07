# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestRepair(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.repair_obj = self.env["repair.order"]
        self.company = self.env.ref("base.main_company")
        self.product = self.env.ref("product.product_product_4")
        self.stock_location_stock = self.env.ref("stock.stock_location_stock")
        self.repair_make_scrap_wiz = self.env["repair_make_scrap.wizard"]
        self.wh = self.env.ref("stock.warehouse0")
        self.scrap_loc = self.env["stock.location"].create(
            {
                "name": "WH Scrap Location",
                "location_id": self.wh.view_location_id.id,
                "scrap_location": True,
            }
        )
        self.repair_type = self.env["repair.type"].create(
            {
                "name": "Scrap Repair",
                "scrap_location_id": self.scrap_loc.id,
            }
        )
        self.lot = self.env["stock.production.lot"].create(
            {
                "name": "lot test",
                "product_id": self.product.id,
                "company_id": self.company.id,
            }
        )
        self._update_product_stock(1, self.lot.id)

    def _update_product_stock(self, qty, lot_id=False, location=None):
        quant = self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": (location.id if location else self.wh.lot_stock_id.id),
                "lot_id": lot_id,
                "inventory_quantity": qty,
            }
        )
        quant.action_apply_inventory()

    def test_01_repair_scrap(self):
        repair = self.repair_obj.create(
            {
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "repair_type_id": self.repair_type.id,
                "location_id": self.stock_location_stock.id,
                "lot_id": self.lot.id,
                "operations": [
                    (
                        0,
                        0,
                        {
                            "name": "TEST",
                            "location_id": self.stock_location_stock.id,
                            "location_dest_id": self.product.property_stock_production.id,
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 50.0,
                            "state": "draft",
                            "type": "add",
                            "company_id": self.company.id,
                            "lot_id": self.lot.id,
                        },
                    )
                ],
            }
        )
        repair.action_validate()
        wizard = self.repair_make_scrap_wiz.with_context(
            **{
                "active_ids": repair.id,
                "active_model": "repair.order",
                "item_ids": [
                    0,
                    0,
                    {
                        "line_id": repair.id,
                        "product_id": repair.product_id.id,
                        "product_qty": repair.product_qty,
                        "location_id": repair.location_id,
                        "uom_id": repair.product_id.uom_id.id,
                    },
                ],
            }
        ).create({})
        action = wizard.action_create_scrap()
        scrap = self.env["stock.scrap"].browse([action["res_id"]])
        self.assertEqual(scrap.location_id.id, self.stock_location_stock.id)
        self.assertEqual(scrap.scrap_location_id.id, self.scrap_loc.id)
        self.assertEqual(scrap.move_id.id, False)
        self.assertEqual(scrap.lot_id.id, self.lot.id)
        scrap.action_validate()
        self.assertEqual(scrap.move_id.product_id.id, self.product.id)
