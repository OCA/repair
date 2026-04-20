# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class RepairOrder(models.Model):

    _inherit = "repair.order"

    def _notify_get_reply_to(self, default=None):
        result = super()._notify_get_reply_to(default=default)
        if custom_repair_email := self.env.context.get("custom_repair_email"):
            for rec in self:
                result[rec.id] = self._notify_get_reply_to_formatted_email(
                    custom_repair_email, rec.display_name
                )
        return result
