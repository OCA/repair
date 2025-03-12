from odoo import Command, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    kit_original_qty = fields.Float(string="Original Kit Quantity", copy=False)

    def write(self, vals):
        """
        When increasing `product_uom_qty` beyond the BoM limit, create a new move
        manually instead of using `_split`, since core Odoo restricts splitting
        for repair moves.
        """
        for move in self:
            if "product_uom_qty" in vals and move.bom_line_id and move.repair_id:
                new_qty = vals["product_uom_qty"]
                max_qty = move.bom_line_id.product_qty * move.kit_original_qty
                if new_qty > max_qty:
                    surplus_qty = new_qty - max_qty
                    new_move_vals = move.copy_data(
                        {
                            "product_uom_qty": surplus_qty,
                            "origin": move.origin,
                            "repair_id": move.repair_id.id,
                            "sale_line_id": False,
                            "bom_line_id": False,
                        }
                    )[0]
                    self.env["stock.move"].create(new_move_vals)
                    vals["product_uom_qty"] = max_qty
        return super().write(vals)

    def _can_form_full_kit(self, moves):
        """
        Determines whether we can form a full kit for the given moves and BoM.
        """
        kit_qty = moves[0].kit_original_qty or 0.0
        return all(
            move.product_uom_qty == move.bom_line_id.product_qty * kit_qty
            for move in moves
            if move.bom_line_id
        )

    def _create_repair_sale_order_line(self):
        """
        Creates sale order lines for repair moves, handling both standard and
        kit-based moves.
        - Groups kit moves by BOM and checks if they form a full kit.
        - Full kits result in a single sale order line.
        - Partial kits are treated as standard moves.
        """
        so_line_vals = []
        grouped_boms = {}

        # 1) Filter out moves that shouldn't create a sale order line
        valid_moves = self.filtered(
            lambda m: not m.sale_line_id
            and m.repair_line_type == "add"
            and m.repair_id.sale_order_id
        )

        # 2) Separate kit moves from standard moves
        kit_moves = valid_moves.filtered(lambda m: m.bom_line_id)
        standard_moves = valid_moves - kit_moves

        # 3) Group BoM kit-related moves
        for move in kit_moves:
            bom_id = move.bom_line_id.bom_id
            grouped_boms.setdefault(bom_id, []).append(move)

        # 4) Process kit-based moves
        for bom, moves in grouped_boms.items():
            is_full = self._can_form_full_kit(moves)

            if not is_full:
                # Partial kit => treat as standard moves
                standard_moves |= self.env["stock.move"].browse([m.id for m in moves])
            else:
                # Full kit => create a single sale order line
                first_move = moves[0]
                kit_qty = first_move.kit_original_qty
                so_line_vals.append(
                    {
                        "order_id": first_move.repair_id.sale_order_id.id,
                        "name": bom.product_tmpl_id.display_name or "Kit",
                        "product_id": bom.product_tmpl_id.product_variant_id.id,
                        "product_uom_qty": kit_qty,
                        "move_ids": [Command.link(m.id) for m in moves],
                        "price_unit": 0.0
                        if first_move.repair_id.under_warranty
                        else first_move.price_unit,
                    }
                )

        # 5) Process standard (non-kit and partial kit) moves using Odoo's logic
        if standard_moves:
            super(StockMove, standard_moves)._create_repair_sale_order_line()

        # 6) Create all sale order lines at once
        if so_line_vals:
            self.env["sale.order.line"].create(so_line_vals)

        return True

    def _prepare_phantom_line_vals(self, bom_line, qty):
        """
        Extend _prepare_phantom_line_vals to include bom_line_id
        """
        vals = super()._prepare_phantom_line_vals(bom_line, qty)
        vals["bom_line_id"] = bom_line.id
        if bom_line.bom_id:
            vals["kit_original_qty"] = self.product_uom_qty
        return vals
