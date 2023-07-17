from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    repair_reason_id = fields.Many2one(
        comodel_name="repair.reason", string="Root Cause"
    )
