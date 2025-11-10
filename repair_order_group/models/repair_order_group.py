# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class RepairOrderGroup(models.Model):
    """Model to group multiple repair orders together."""

    _name = "repair.order.group"
    _description = "Repair Order Group"

    name = fields.Char(
        required=True,
        default=lambda self: _("New"),
        copy=False,
    )
    partner_id = fields.Many2one("res.partner", required=True, string="Customer")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    repair_ids = fields.One2many("repair.order", "group_id", string="Repairs")
    repair_count = fields.Integer(compute="_compute_repair_count", store=True)

    @api.depends("repair_ids")
    def _compute_repair_count(self):
        """Compute the number of repair orders in this group."""
        for group in self:
            group.repair_count = len(group.repair_ids)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "name" in fields_list and not res.get("name"):
            res["name"] = (
                self.env["ir.sequence"].next_by_code("repair.order.group") or "New"
            )
        return res
