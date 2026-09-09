# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    add_grouped_repair_state_ids = fields.Many2many(
        comodel_name="ir.model.fields.selection",
        relation="res_company_add_grouped_repair_state_rel",
        column1="company_id",
        column2="selection_id",
        string="Add Grouped Repair Available In",
        default=lambda self: self._default_add_grouped_repair_state_ids(),
        domain=[
            ("field_id.model", "=", "repair.order"),
            ("field_id.name", "=", "state"),
        ],
    )

    @api.model
    def _default_add_grouped_repair_state_ids(self):
        """Return the default state for Add Grouped Repair availability."""
        return (
            self.env["ir.model.fields.selection"]
            .sudo()
            .search(
                [
                    ("field_id.model", "=", "repair.order"),
                    ("field_id.name", "=", "state"),
                    ("value", "=", "draft"),
                ],
                limit=1,
                order="sequence, id",
            )
        )
