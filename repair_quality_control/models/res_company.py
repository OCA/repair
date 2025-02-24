# Copyright 2024 ForgeFlow (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    repair_auto_generate_qc_inspection = fields.Boolean(
        string="Auto-generate QC Inspection",
        help="If checked, QC Inspections will be automatically "
        "created for Repair Order, on state changes.",
    )

    repair_generate_qc_inspection_state = fields.Selection(
        [
            ("confirmed", "On Confirm"),
            ("done", "On Done"),
        ],
        string="Generate QC Inspection State",
        default="done",
        required=True,
        help="This field allows you to select the state of the Repair "
        "Order in which the QC Inspection will be generated.",
    )
