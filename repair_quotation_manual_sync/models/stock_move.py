# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    repair_invoiceable = fields.Boolean(
        "Invoiceable",
        help="Check this box if the product is billable. "
        "Only invoiceable products will be included in the quotation.",
        default=True,
    )
    repair_create_sync = fields.Boolean(
        compute="_compute_sync_flags",
    )
    repair_update_sync = fields.Boolean(
        compute="_compute_sync_flags",
    )
    is_repair_sale_confirmed = fields.Boolean(
        compute="_compute_is_repair_sale_confirmed",
    )

    @api.depends("repair_id.sale_order_id.state")
    def _compute_is_repair_sale_confirmed(self):
        for move in self:
            move.is_repair_sale_confirmed = (
                move.repair_id.sale_order_id.state == "sale"
                if move.repair_id and move.repair_id.sale_order_id
                else False
            )

    @api.depends(
        "repair_invoiceable",
        "sale_line_id",
        "product_id",
        "product_uom_qty",
        "sale_line_id.product_id",
        "sale_line_id.product_uom_qty",
    )
    def _compute_sync_flags(self):
        for move in self:
            precision = move.product_uom.rounding
            move.repair_create_sync = (
                move.repair_invoiceable
                and not move.sale_line_id
                and not float_is_zero(
                    move.product_uom_qty, precision_rounding=precision
                )
            )
            move.repair_update_sync = move.sale_line_id and (
                move.product_id != move.sale_line_id.product_id
                or float_compare(
                    move.product_uom_qty,
                    move.sale_line_id.product_uom_qty,
                    precision_rounding=precision,
                )
                != 0
                or not move.repair_invoiceable
            )

    def write(self, vals):
        sale_lines = {}
        if "product_id" in vals:
            for move in self:
                if move.repair_id and move.sale_line_id:
                    sale_lines[move.id] = move.sale_line_id
        moves = self
        if sale_lines:
            moves = self.with_context(repair_lines_manual_sync=False)
        res = super(StockMove, moves).write(vals)
        for move in self.browse(sale_lines.keys()):
            if not move.sale_line_id:
                move.sale_line_id = sale_lines[move.id]
        return res

    def _create_repair_sale_order_line(self):
        if not self.env.context.get("repair_lines_manual_sync", False):
            return True
        return super(
            StockMove, self.filtered("repair_create_sync")
        )._create_repair_sale_order_line()

    def _update_repair_sale_order_line(self):
        if not self.env.context.get("repair_lines_manual_sync", False):
            return True
        moves_to_sync = self.filtered("repair_update_sync")
        moves_product_changed = moves_to_sync.filtered(
            lambda m: m.repair_line_type == "add"
            and m.repair_invoiceable
            and m.product_id != m.sale_line_id.product_id
        )
        sequences = {m.id: m.sale_line_id.sequence for m in moves_product_changed}
        moves_product_changed.sale_line_id.unlink()
        moves_product_changed.invalidate_recordset()
        moves_product_changed._create_repair_sale_order_line()
        for move in moves_product_changed:
            move.sale_line_id.sequence = sequences[move.id]
        super(
            StockMove, moves_to_sync - moves_product_changed
        )._update_repair_sale_order_line()
        moves_so_line_unlink = self.filtered(
            lambda m: m.sale_line_id
            and (
                not m.repair_invoiceable
                or float_is_zero(
                    m.product_uom_qty, precision_rounding=m.product_uom.rounding
                )
            )
        )
        moves_so_line_unlink._clean_repair_sale_order_line()
        return True
