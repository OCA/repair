# Copyright 2024 360ERP (<https://www.360erp.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BaseSubstateType(models.Model):
    _inherit = "base.substate.type"

    model = fields.Selection(
        selection_add=[("repair.order", "Repair order")],
        ondelete={"repair.order": "cascade"},
    )


class RepairOrder(models.Model):
    _inherit = ["repair.order", "base.substate.mixin"]
    _name = "repair.order"

    @api.constrains("substate_id", "state")
    def check_substate_id_value(self):
        repair_states = dict(self._fields["state"].selection)
        for order in self:
            target_state = order.substate_id.target_state_value_id.target_state_value
            if order.substate_id and order.state != target_state and target_state:
                raise ValidationError(
                    _(
                        "The substate %(name)s is not defined for the state"
                        " %(state)s but for %(target_state)s "
                    )
                    % {
                        "name": order.substate_id.name,
                        "state": _(repair_states[order.state]),
                        "target_state": _(repair_states[target_state]),
                    }
                )

    def _track_template(self, changes):
        res = super()._track_template(changes)
        track = self[0]
        if "substate_id" in changes and track.substate_id.mail_template_id:
            res["substate_id"] = (
                track.substate_id.mail_template_id,
                {
                    "composition_mode": "comment",
                    "auto_delete_message": True,
                    "subtype_id": self.env["ir.model.data"]._xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                },
            )
        return res
