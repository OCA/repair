# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestRepairAnalyticDistribution(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.analytic_plan = cls.env.ref("repair_analytic.analytic_plan_repair_demo")
        cls.analytic_account = cls.env.ref(
            "repair_analytic.analytic_account_repair_demo"
        )
        cls.analytic_account_2 = cls.env.ref(
            "repair_analytic.analytic_account_repair_demo_2"
        )
        cls.analytic_applicability = cls.env.ref(
            "repair_analytic.analytic_applicability_repair_demo"
        )
        cls.analytic_distribution = {str(cls.analytic_account.id): 100.0}

        cls.product_to_repair = cls.env.ref("product.product_product_5")
        cls.product_add = cls.env.ref("repair_analytic.product_repair_demo_add")
        cls.product_remove = cls.env.ref("repair_analytic.product_repair_demo_remove")
        cls.product_recycle = cls.env.ref("repair_analytic.product_repair_demo_recycle")

        cls.repair_type = cls.env.ref("repair.picking_type_warehouse0_repair")

    def _make_repair(self, analytic_distribution=None, price_type="cost"):
        self.repair_type.write({"analytic_price_type": price_type})
        return self.env["repair.order"].create(
            {
                "product_id": self.product_to_repair.id,
                "picking_type_id": self.repair_type.id,
                "analytic_distribution": (
                    analytic_distribution
                    if analytic_distribution is not None
                    else self.analytic_distribution
                ),
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.product_add.id,
                            "product_uom_qty": 2.0,
                            "repair_line_type": "add",
                            "company_id": self.env.company.id,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product_remove.id,
                            "product_uom_qty": 3.0,
                            "repair_line_type": "remove",
                            "company_id": self.env.company.id,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product_recycle.id,
                            "product_uom_qty": 1.0,
                            "repair_line_type": "recycle",
                            "company_id": self.env.company.id,
                        }
                    ),
                ],
            }
        )

    def _complete_repair(self, repair):
        repair._action_repair_confirm()
        repair.action_repair_start()
        for move in repair.move_ids:
            move.quantity = move.product_uom_qty
        repair.action_repair_end()

    def _analytic_lines(self, repair):
        return self.env["account.analytic.line"].search(
            [("repair_order_id", "=", repair.id)]
        )

    def test_analytic_lines_created_on_done(self):
        """Completing a repair creates one analytic line per part move."""
        repair = self._make_repair()
        self._complete_repair(repair)

        lines = self._analytic_lines(repair)
        self.assertEqual(
            len(lines),
            3,
            "Expected one analytic line per part move (add, remove, recycle).",
        )

    def test_no_analytic_lines_without_distribution(self):
        """No analytic lines are created when analytic_distribution is empty."""
        repair = self._make_repair(analytic_distribution=False)
        self._complete_repair(repair)

        self.assertFalse(
            self._analytic_lines(repair),
            "No analytic lines expected when distribution is not set.",
        )

    def test_analytic_lines_sign_per_move_type(self):
        """add → negative; remove and recycle → positive."""
        repair = self._make_repair()
        self._complete_repair(repair)

        cases = [
            ("add", self.product_add, -1),
            ("remove", self.product_remove, 1),
            ("recycle", self.product_recycle, 1),
        ]
        for line_type, product, expected_sign in cases:
            with self.subTest(repair_line_type=line_type):
                line = self._analytic_lines(repair).filtered(
                    lambda al, p=product: al.product_id == p
                )
                self.assertEqual(len(line), 1)
                self.assertEqual(
                    (1 if line.amount > 0 else -1),
                    expected_sign,
                    f"Wrong sign for repair_line_type='{line_type}'.",
                )

    def test_analytic_amount_uses_standard_price(self):
        """With price_type='cost', amount = standard_price × quantity × sign."""
        repair = self._make_repair(price_type="cost")
        self._complete_repair(repair)

        cases = [
            (self.product_add, "add", -1),
            (self.product_remove, "remove", 1),
            (self.product_recycle, "recycle", 1),
        ]
        for product, line_type, sign in cases:
            with self.subTest(repair_line_type=line_type):
                move = repair.move_ids.filtered(lambda m, p=product: m.product_id == p)
                line = self._analytic_lines(repair).filtered(
                    lambda al, p=product: al.product_id == p
                )
                expected = sign * product.standard_price * move.quantity
                self.assertAlmostEqual(
                    line.amount,
                    expected,
                    places=2,
                    msg=(
                        f"Wrong amount for repair_line_type='{line_type}'"
                        " with cost type."
                    ),
                )

    def test_analytic_amount_uses_price_unit(self):
        """With price_type='price' and no SO, amount = move.price_unit × qty × sign."""
        repair = self._make_repair(price_type="price")
        # Without a linked sale order, price_unit must be set explicitly on the move.
        add_move = repair.move_ids.filtered(lambda m: m.repair_line_type == "add")
        add_move.price_unit = 50.0

        self._complete_repair(repair)

        line = self._analytic_lines(repair).filtered(
            lambda al: al.product_id == self.product_add
        )
        expected = -1 * 50.0 * add_move.quantity
        self.assertAlmostEqual(line.amount, expected, places=2)

    def test_analytic_amount_uses_sale_line_price_unit(self):
        """With price_type='price' and a linked SO line, amount uses SO line price."""
        repair = self._make_repair(price_type="price")
        add_move = repair.move_ids.filtered(lambda m: m.repair_line_type == "add")

        partner = self.env["res.partner"].search([], limit=1)
        sale_order = self.env["sale.order"].create({"partner_id": partner.id})
        sol = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product_add.id,
                "product_uom_qty": 2.0,
                "price_unit": 70.0,
            }
        )
        add_move.sale_line_id = sol

        self._complete_repair(repair)

        line = self._analytic_lines(repair).filtered(
            lambda al: al.product_id == self.product_add
        )
        expected = -1 * 70.0 * add_move.quantity
        self.assertAlmostEqual(line.amount, expected, places=2)

    def test_analytic_amount_distribution_percentage(self):
        """With 60/40% split across two accounts, amount is proportional."""
        distribution = {
            str(self.analytic_account.id): 60.0,
            str(self.analytic_account_2.id): 40.0,
        }
        repair = self._make_repair(
            analytic_distribution=distribution, price_type="cost"
        )
        self._complete_repair(repair)

        lines = self._analytic_lines(repair)
        # 3 moves × 2 accounts = 6 lines
        self.assertEqual(len(lines), 6)

        add_move = repair.move_ids.filtered(lambda m: m.repair_line_type == "add")
        total_expected = -1 * self.product_add.standard_price * add_move.quantity

        add_lines = lines.filtered(lambda al: al.product_id == self.product_add)
        with self.subTest(account="primary_60pct"):
            primary = add_lines.filtered(
                lambda al: al[self.analytic_plan._column_name()]
                == self.analytic_account
            )
            self.assertAlmostEqual(primary.amount, total_expected * 0.6, places=2)

        with self.subTest(account="secondary_40pct"):
            secondary = add_lines.filtered(
                lambda al: al[self.analytic_plan._column_name()]
                == self.analytic_account_2
            )
            self.assertAlmostEqual(secondary.amount, total_expected * 0.4, places=2)

    def test_analytic_distribution_accounts_from_different_plans_share_one_line(self):
        """A comma-separated key combines accounts from different plans on
        a single analytic line instead of creating one line per account."""
        other_plan = self.env["account.analytic.plan"].create(
            {"name": "Other Test Plan"}
        )
        other_account = self.env["account.analytic.account"].create(
            {"name": "Other Plan Account", "plan_id": other_plan.id}
        )
        distribution = {
            f"{self.analytic_account.id},{other_account.id}": 100.0,
        }
        repair = self._make_repair(
            analytic_distribution=distribution, price_type="cost"
        )
        self._complete_repair(repair)

        lines = self._analytic_lines(repair)
        # One line per move (not one per account), since both accounts share
        # the same distribution key.
        self.assertEqual(len(lines), 3)

        add_line = lines.filtered(lambda al: al.product_id == self.product_add)
        self.assertEqual(len(add_line), 1)
        self.assertEqual(
            add_line[self.analytic_plan._column_name()], self.analytic_account
        )
        self.assertEqual(
            add_line[other_plan._column_name()],
            other_account,
            "The line should also carry the account from the second plan.",
        )

    def test_analytic_distribution_skips_nonexistent_accounts(self):
        """A distribution key pointing to a non-existent account id
        contributes no analytic line."""
        distribution = {"999999999": 100.0}
        repair = self._make_repair(
            analytic_distribution=distribution, price_type="cost"
        )
        self._complete_repair(repair)

        self.assertFalse(
            self._analytic_lines(repair),
            "No analytic line should be created for a non-existent account id.",
        )

    def test_moves_without_repair_line_type_are_excluded(self):
        """Only moves with a repair_line_type set are turned into analytic
        lines, even if they reach the 'done' state.

        Exercises `_create_analytic_lines` directly, bypassing the button
        workflow, since a move without a repair_line_type cannot be driven
        to 'done' through the normal Parts-tab flow.
        """
        repair = self._make_repair()
        repair.write({"analytic_distribution": self.analytic_distribution})
        repair.move_ids.write({"state": "done", "quantity": 1.0})
        self.env["stock.move"].create(
            {
                "name": "Extra move without a repair line type",
                "repair_id": repair.id,
                "product_id": self.product_to_repair.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_to_repair.uom_id.id,
                "location_id": repair.location_id.id,
                "location_dest_id": repair.location_dest_id.id,
                "company_id": self.env.company.id,
                "state": "done",
                "quantity": 1.0,
            }
        )

        repair._create_analytic_lines()

        lines = self._analytic_lines(repair)
        self.assertEqual(
            len(lines),
            3,
            "The move without a repair_line_type must not generate a line.",
        )
        self.assertNotIn(self.product_to_repair, lines.mapped("product_id"))

    def test_analytic_lines_deleted_on_cancel(self):
        """Cancelling a repair deletes its linked analytic lines."""
        repair = self._make_repair()
        self.env["account.analytic.line"].sudo().create(
            [
                {
                    "name": repair.name,
                    "repair_order_id": repair.id,
                    "company_id": repair.company_id.id,
                    self.analytic_plan._column_name(): self.analytic_account.id,
                },
                {
                    "name": repair.name,
                    "repair_order_id": repair.id,
                    "company_id": repair.company_id.id,
                    self.analytic_plan._column_name(): self.analytic_account.id,
                },
            ]
        )
        self.assertEqual(len(self._analytic_lines(repair)), 2)

        repair.action_repair_cancel()

        self.assertFalse(
            self._analytic_lines(repair),
            "Analytic lines must be deleted when repair is cancelled.",
        )

    def test_analytic_lines_deleted_on_unlink(self):
        """Deleting a repair order also removes its analytic lines."""
        repair = self._make_repair()
        self.env["account.analytic.line"].sudo().create(
            {
                "name": repair.name,
                "repair_order_id": repair.id,
                "company_id": repair.company_id.id,
                self.analytic_plan._column_name(): self.analytic_account.id,
            }
        )
        repair_id = repair.id
        self.assertEqual(
            self.env["account.analytic.line"].search_count(
                [("repair_order_id", "=", repair_id)]
            ),
            1,
        )

        repair.unlink()

        self.assertEqual(
            self.env["account.analytic.line"].search_count(
                [("repair_order_id", "=", repair_id)]
            ),
            0,
            "Analytic lines must be deleted when the repair order is removed.",
        )

    def test_analytic_line_count(self):
        """analytic_line_count reflects the number of linked analytic lines."""
        repair = self._make_repair()

        self.assertEqual(repair.analytic_line_count, 0)

        self._complete_repair(repair)

        self.assertEqual(repair.analytic_line_count, 3)

    def test_action_view_analytic_lines_returns_correct_domain(self):
        """Smart button action filters lines by the current repair."""
        repair = self._make_repair()
        self._complete_repair(repair)

        action = repair.action_view_analytic_lines()

        self.assertEqual(action["res_model"], "account.analytic.line")
        self.assertIn(("repair_order_id", "=", repair.id), action["domain"])

    def test_analytic_plan_business_domain_includes_repair(self):
        """'repair' is available as a business domain in analytic applicability."""
        self.assertEqual(self.analytic_applicability.business_domain, "repair")

    def test_analytic_picking_type_price_type_field(self):
        """analytic_price_type is selectable on a repair operation type."""
        for price_type in ("price", "cost"):
            with self.subTest(price_type=price_type):
                self.repair_type.write({"analytic_price_type": price_type})
                self.assertEqual(self.repair_type.analytic_price_type, price_type)

    def test_analytic_picking_type_price_type_default(self):
        """analytic_price_type defaults to 'price' on a new operation type."""
        new_type = self.env["stock.picking.type"].create(
            {
                "name": "Test Repair Type",
                "code": "repair_operation",
                "sequence_code": "TRT",
                "company_id": self.env.company.id,
                "warehouse_id": self.repair_type.warehouse_id.id,
            }
        )
        self.assertEqual(new_type.analytic_price_type, "price")

    def test_duplicate_repair_order(self):
        """Duplicating a repair order with parts and an analytic
        distribution must not raise."""
        repair = self._make_repair()
        self._complete_repair(repair)

        duplicate = repair.copy()

        self.assertNotEqual(duplicate.id, repair.id)
        self.assertEqual(duplicate.analytic_distribution, repair.analytic_distribution)

    def test_duplicate_repair_order_keeps_price_unit(self):
        """Price must survive duplication of a repair order.

        stock.move.price_unit is declared copy=False in core stock, since
        for ordinary stock moves it's transient valuation data. On repair
        parts it is user-facing Price data and must be preserved.
        """
        repair = self._make_repair(price_type="price")
        add_move = repair.move_ids.filtered(lambda m: m.repair_line_type == "add")
        add_move.price_unit = 42.0

        duplicate = repair.copy()

        duplicate_add_move = duplicate.move_ids.filtered(
            lambda m: m.repair_line_type == "add"
        )
        self.assertEqual(duplicate_add_move.price_unit, 42.0)


class TestRepairAnalyticStockMove(TransactionCase):
    """Coverage for the Price/Cost fields and defaulting logic added on
    stock.move for repair consumed items (Parts)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.repair_type = cls.env.ref("repair.picking_type_warehouse0_repair")
        cls.product_to_repair = cls.env.ref("product.product_product_5")
        cls.product_add = cls.env.ref("repair_analytic.product_repair_demo_add")
        cls.product_remove = cls.env.ref("repair_analytic.product_repair_demo_remove")

    def _make_repair(self):
        return self.env["repair.order"].create(
            {
                "product_id": self.product_to_repair.id,
                "picking_type_id": self.repair_type.id,
            }
        )

    def test_cost_field_mirrors_product_standard_price(self):
        """The 'cost' field is a live related to product_id.standard_price."""
        repair = self._make_repair()
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(move.cost, self.product_add.standard_price)

        self.product_add.standard_price = 999.0
        self.assertEqual(
            move.cost, 999.0, "cost must follow live changes to standard_price."
        )

    def test_company_currency_id_related_to_company_currency(self):
        """company_currency_id mirrors company_id.currency_id."""
        repair = self._make_repair()
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(move.company_currency_id, self.env.company.currency_id)

    def test_price_unit_onchange_defaults_from_list_price(self):
        """Picking a product on an 'add' line defaults Price from the
        product's Sales Price.

        The Price field is read-only in the Parts list (users must not
        hand-edit the computed default), so this is exercised as a direct
        onchange call rather than through Form(): Form's readonly handling
        does not reflect how the real webclient still applies onchange
        results to readonly fields, so it would not be a faithful test.
        """
        repair = self._make_repair()
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
            }
        )
        move._onchange_product_id_repair_analytic_price_unit()
        self.assertEqual(move.price_unit, self.product_add.list_price)

    def test_price_unit_onchange_does_not_override_manual_value(self):
        """A manually-typed Price is not clobbered by the default."""
        repair = self._make_repair()
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
                "price_unit": 12.5,
            }
        )
        move._onchange_product_id_repair_analytic_price_unit()
        self.assertEqual(move.price_unit, 12.5)

    def test_price_unit_onchange_not_applied_to_remove_or_recycle(self):
        """Only 'add' lines get an auto-filled Price."""
        repair = self._make_repair()
        for line_type in ("remove", "recycle"):
            with self.subTest(repair_line_type=line_type):
                move = self.env["stock.move"].create(
                    {
                        "repair_id": repair.id,
                        "repair_line_type": line_type,
                        "product_id": self.product_add.id,
                        "product_uom_qty": 1.0,
                        "product_uom": self.product_add.uom_id.id,
                        "company_id": self.env.company.id,
                    }
                )
                move._onchange_product_id_repair_analytic_price_unit()
                self.assertEqual(move.price_unit, 0.0)

    def test_price_unit_onchange_not_applied_when_sale_line_linked(self):
        """A move already tied to a sale.order.line keeps its own pricing
        flow and is not overwritten by the Sales Price default."""
        repair = self._make_repair()
        partner = self.env["res.partner"].search([], limit=1)
        sale_order = self.env["sale.order"].create({"partner_id": partner.id})
        sol = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "price_unit": 70.0,
            }
        )
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
                "sale_line_id": sol.id,
            }
        )
        move._onchange_product_id_repair_analytic_price_unit()
        self.assertEqual(move.price_unit, 0.0)

    def test_price_unit_defaults_on_create_without_onchange(self):
        """create() alone (no onchange call) must default Price.

        Price is read-only, so the client cannot be relied on to persist
        the onchange-computed value once the row is edited further (e.g.
        typing Quantity after picking the product) before saving. The
        server-side create() is the authoritative guarantee.
        """
        repair = self._make_repair()
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(move.price_unit, self.product_add.list_price)

    def test_price_unit_create_does_not_override_manual_value(self):
        """create() must not clobber an explicitly-passed Price."""
        repair = self._make_repair()
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "add",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
                "price_unit": 12.5,
            }
        )
        self.assertEqual(move.price_unit, 12.5)

    def test_price_unit_defaults_on_write_when_line_type_becomes_add(self):
        """Changing repair_line_type to 'add' via write() also defaults
        Price, for the same read-only-field reason as create()."""
        repair = self._make_repair()
        move = self.env["stock.move"].create(
            {
                "repair_id": repair.id,
                "repair_line_type": "remove",
                "product_id": self.product_add.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_add.uom_id.id,
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(move.price_unit, 0.0)

        move.write({"repair_line_type": "add"})

        self.assertEqual(move.price_unit, self.product_add.list_price)
