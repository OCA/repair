# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("to_refurbish"):
            return super().create(vals_list)

        refurbish_scrap_loc = self.env.ref(
            "repair_refurbish.stock_location_refurbish_scrap"
        )

        # browse only once (instead of each iteration of the loop)
        repairs = self.env["repair.order"].browse(
            {v.get("repair_id") for v in vals_list if v.get("repair_id")}
        )
        repair_map = {r.id: r for r in repairs}

        for vals in vals_list:
            # Only change the location_dest of the main repair order move
            repair_id = vals.get("repair_id")
            product_id = vals.get("product_id")
            if not repair_id:
                continue
            repair = repair_map[repair_id]
            if product_id != repair.product_id.id:
                continue

            vals["location_dest_id"] = refurbish_scrap_loc.id

            # we must also update the lines to prevent destination mismatch.
            if vals.get("move_line_ids"):
                for line in vals["move_line_ids"]:
                    # line format: (0, 0, {values})
                    if (
                        isinstance(line, (list, tuple))
                        and len(line) == 3
                        and isinstance(line[2], dict)
                    ):
                        line[2]["location_dest_id"] = refurbish_scrap_loc.id

        return super().create(vals_list)
