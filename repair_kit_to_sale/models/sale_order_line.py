from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_qty_delivered(self):
        remaining_so_lines = self
        for so_line in self:
            moves = so_line.move_ids.sudo().filtered(
                lambda m: m.repair_id and m.state == "done"
            )
            if not moves:
                continue
            product = so_line.product_id
            bom = (
                self.env["mrp.bom"]._bom_find(product, bom_type="phantom").get(product)
                if product
                else None
            )

            if moves[0].kit_original_qty and bom:
                bom_requirements = {
                    line.product_id: line.product_qty for line in bom.bom_line_ids
                }
                min_possible_kits = None
                for move in moves:
                    required_qty = bom_requirements.get(move.product_id, 0)
                    if required_qty > 0:
                        possible_kits = move.quantity // required_qty
                        min_possible_kits = (
                            possible_kits
                            if min_possible_kits is None
                            else min(min_possible_kits, possible_kits)
                        )
                qty_delivered = (
                    int(min_possible_kits) if min_possible_kits is not None else 0
                )
            else:
                if len(moves) == 1:
                    qty_delivered = moves.quantity
                else:
                    continue
            remaining_so_lines -= so_line
            so_line.qty_delivered = qty_delivered
        return super(SaleOrderLine, remaining_so_lines)._compute_qty_delivered()
