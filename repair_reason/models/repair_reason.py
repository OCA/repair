from odoo import fields, models


class RepairReason(models.Model):

    _name = "repair.reason"
    _description = "Repair Reason"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    name = fields.Char(
        string="Root Cause",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
