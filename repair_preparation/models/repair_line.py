# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairLine(models.Model):
    _inherit = "repair.line"

    preparation_move_ids = fields.One2many(
        comodel_name="stock.move",
        inverse_name="repair_line_id",
    )

    @api.depends("type", "repair_id.location_id")
    def _compute_location_id(self):
        res = super()._compute_location_id()
        for rec in self:
            if rec.type == "add" and rec.repair_id.location_id:
                rec.location_id = rec.repair_id.location_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for repair in records.repair_id:
            if repair.state != "under_repair":
                # we manage procurement auto-run when repair is started
                continue
            new_lines = records.filtered(lambda line, ro=repair: line.repair_id == ro)
            repair._run_preparation_procurements(new_lines)
        return records

    def write(self, vals):
        res = super().write(vals)
        fields_affecting = {"type", "product_id", "product_uom_qty", "product_uom"}
        if all(_field not in vals for _field in fields_affecting):
            return res
        for repair in self.repair_id:
            updated_lines = self.filtered(lambda line, ro=repair: line.repair_id == ro)
            if not updated_lines:
                continue
            moves = updated_lines.preparation_move_ids
            if moves.filtered(lambda m: m.state == "done"):
                raise ValidationError(
                    _(
                        "You cannot modify product/quantity for preparation lines "
                        "because some linked moves are already done.\n"
                        "Repair: %(repair)s\nLines: %(lines)s",
                        repair=repair.display_name,
                        lines=", ".join(updated_lines.mapped("display_name")),
                    )
                )
            if repair.state != "under_repair":
                # we manage procurement auto-run when repair is started
                continue
            moves_to_cancel = moves.filtered(lambda m: m.state != "cancel")
            moves_to_cancel._action_cancel()
            repair._run_preparation_procurements(updated_lines)

        return res
