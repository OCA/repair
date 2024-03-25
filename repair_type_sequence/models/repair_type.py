# Copyright 2023 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RepairType(models.Model):
    _inherit = "repair.type"

    sequence_prefix = fields.Char(
        help="The rorder's sequence will be created using this prefix.",
    )
    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Entry Sequence",
        help="This field contains the information related to the "
        "numbering of the rorders belonging to this rtype.",
        copy=False,
    )
    sequence_number_next = fields.Integer(
        string="Next Number",
        help="The next sequence number will be used for the next rorder.",
        compute="_compute_seq_number_next",
        inverse="_inverse_seq_number_next",
    )

    @api.model
    def _create_sequence(self, vals):
        """Create new no_gap entry sequence"""
        seq = {
            "name": vals.get("name", False) or self.name,
            "implementation": "no_gap",
            "prefix": (vals.get("sequence_prefix", False) or self.sequence_prefix),
            "padding": 4,
            "number_increment": 1,
            "use_date_range": False,
        }
        seq = self.env["ir.sequence"].create(seq)
        seq_date_range = seq._get_current_sequence()
        seq_date_range.number_next = vals.get("sequence_number_next", 1)
        return seq

    # do not depend on 'sequence_id.date_range_ids', because
    # sequence_id._get_current_sequence() may invalidate it!
    @api.depends("sequence_id.use_date_range", "sequence_id.number_next_actual")
    def _compute_seq_number_next(self):
        """Compute 'sequence_number_next' according to the current sequence
        in use, an ir.sequence or an ir.sequence.date_range.
        """
        for rtype in self:
            if rtype.sequence_id:
                sequence = rtype.sequence_id._get_current_sequence()
                rtype.sequence_number_next = sequence.number_next_actual
            else:
                rtype.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        """
        Inverse 'sequence_number_next' to edit the current sequence next number
        """
        for rtype in self:
            if rtype.sequence_id and rtype.sequence_number_next:
                sequence = rtype.sequence_id._get_current_sequence()
                sequence.sudo().number_next = rtype.sequence_number_next

    @api.model
    def create(self, vals):
        if not vals.get("sequence_id", False):
            if vals.get("sequence_prefix", False):
                vals["sequence_id"] = self.sudo()._create_sequence(vals).id
        else:
            vals["sequence_prefix"] = (
                self.env["ir.sequence"].browse(vals["sequence_id"]).prefix
            )
        result = super(RepairType, self).create(vals)
        self._compute_rorder_code()
        return result

    def write(self, vals):
        if not vals.get("sequence_id", False):
            if vals.get("sequence_prefix", False):
                vals["sequence_id"] = self.sudo()._create_sequence(vals).id
        else:
            vals["sequence_prefix"] = (
                self.env["ir.sequence"].browse(vals["sequence_id"]).prefix
            )
        result = super(RepairType, self).write(vals)
        self._compute_rorder_code()
        return result

    @api.onchange("sequence_id")
    def _onchange_sequence_id(self):
        if self.sequence_id:
            self.sequence_prefix = self.sequence_id.prefix

    def _compute_rorder_code(self):
        for rtype in self:
            if rtype.sequence_id:
                rtype_rorders = rtype.env["repair.order"].search(
                    [("repair_type_id", "=", rtype.id)]
                )
                for rorder in rtype_rorders:
                    if not rorder.name and rorder.repair_type_id.sequence_id:
                        rorder.name = rorder.repair_type_id.sequence_id._next()
