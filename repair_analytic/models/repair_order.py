# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class RepairOrder(models.Model):
    _name = "repair.order"
    _inherit = ["repair.order", "analytic.mixin"]

    analytic_line_count = fields.Integer(
        compute="_compute_analytic_line_count",
        string="Analytic Lines",
    )

    def _compute_analytic_line_count(self):
        for repair in self:
            repair.analytic_line_count = self.env["account.analytic.line"].search_count(
                [("repair_order_id", "=", repair.id)]
            )

    def action_view_analytic_lines(self):
        self.ensure_one()
        list_view = self.env.ref("analytic.view_account_analytic_line_tree")
        form_view = self.env.ref("analytic.view_account_analytic_line_form")
        search_view = self.env.ref(
            "repair_analytic.view_account_analytic_line_search_repair"
        )
        return {
            "name": _("Analytic Lines"),
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "views": [(list_view.id, "list"), (form_view.id, "form")],
            "search_view_id": search_view.id,
            "domain": [("repair_order_id", "=", self.id)],
        }

    def _get_analytic_unit_price(self, move):
        if self.picking_type_id.analytic_price_type == "cost":
            return move.product_id.standard_price
        if move.sale_line_id:
            return move.sale_line_id.price_unit
        return move.price_unit

    def _prepare_analytic_line_vals_for_move(self, move):
        """
        Convert analytic_distribution JSON to account.analytic.line vals list.

        Sign convention:
          add     → -1  (part consumed = cost)
          remove  → +1  (part recovered = reversal)
          recycle → +1  (part recovered = reversal)

        JSON format: {"account_ids_csv": percentage}
        e.g. {"15": 100} or {"14,16": 60, "17": 40}
        A comma-separated key means accounts from different plans share one line.
        """
        if not self.analytic_distribution:
            return []

        sign = -1 if move.repair_line_type == "add" else 1
        unit_price = self._get_analytic_unit_price(move)
        quantity = move.quantity
        total = sign * unit_price * quantity

        vals_list = []
        for account_ids_str, percentage in self.analytic_distribution.items():
            account_field_values = {}
            account_ids = [
                int(a) for a in account_ids_str.split(",") if a.strip().isdigit()
            ]
            for account in (
                self.env["account.analytic.account"].browse(account_ids).exists()
            ):
                account_field_values[account.plan_id._column_name()] = account.id
            if not account_field_values:
                continue

            vals_list.append(
                {
                    "name": self.name,
                    "date": fields.Date.context_today(self),
                    "unit_amount": quantity,
                    "amount": total * float(percentage) / 100.0,
                    "product_id": move.product_id.id,
                    "product_uom_id": move.product_uom.id,
                    "company_id": self.company_id.id,
                    "repair_order_id": self.id,
                    **account_field_values,
                }
            )
        return vals_list

    def _create_analytic_lines(self):
        all_vals = []
        for repair in self.filtered("analytic_distribution"):
            for move in repair.move_ids.filtered(
                lambda m: m.state == "done" and m.repair_line_type
            ):
                all_vals.extend(repair._prepare_analytic_line_vals_for_move(move))
        if all_vals:
            self.env["account.analytic.line"].sudo().create(all_vals)
        self.invalidate_recordset(["analytic_line_count"])

    def _delete_analytic_lines(self):
        self.env["account.analytic.line"].sudo().search(
            [("repair_order_id", "in", self.ids)]
        ).unlink()
        self.invalidate_recordset(["analytic_line_count"])

    def action_repair_done(self):
        result = super().action_repair_done()
        self._create_analytic_lines()
        return result

    def action_repair_cancel(self):
        result = super().action_repair_cancel()
        self._delete_analytic_lines()
        return result

    def unlink(self):
        self._delete_analytic_lines()
        return super().unlink()
