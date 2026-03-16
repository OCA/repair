# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import _, fields, models
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    repair_group_id = fields.Many2one(
        "repair.group",
        string="Repair Group (Picking)",
        ondelete="set null",
        copy=False,
    )
    state = fields.Selection(
        selection_add=[
            ("to_approve", "To Approve"),
        ],
        ondelete={"to_approve": "set default"},
    )

    def action_request_approval(self):
        self.ensure_one()
        if not self.repair_group_id:
            raise UserError(_("This repair order is not part of a group."))

        if (
            self.env.user != self.repair_group_id.supervisor_id
            and self.env.user != self.user_id
        ):
            raise UserError(
                _(
                    "Only the supervisor and the responsible can request approval "
                    "for this repair."
                )
            )
        return self.write({"state": "to_approve"})

    def action_supervisor_approve(self):
        self.ensure_one()
        if self.env.user != self.repair_group_id.supervisor_id:
            raise UserError(_("Only the supervisor can approve this repair."))

        # We temporarily set to draft to allow standard validation if it has constraints
        self.write({"state": "draft"})
        return self.action_validate()

    def action_supervisor_reject(self):
        self.ensure_one()
        if self.env.user != self.repair_group_id.supervisor_id:
            raise UserError(_("Only the supervisor can reject this repair."))

        self.message_post(
            body=_("Repair rejected by supervisor. Please review it."),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
            partner_ids=[self.user_id.partner_id.id] if self.user_id else [],
        )
        return self.write({"state": "draft"})

    def action_print_repair_order(self):
        return self.env.ref("repair.action_report_repair_order").report_action(self)
