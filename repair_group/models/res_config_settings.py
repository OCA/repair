# Copyright 2026 Grupo Isonor - Abel Suárez
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import SUPERUSER_ID, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_stock_tracking_owner = fields.Boolean(
        "Consignment",
        implied_group="stock.group_tracking_owner",
        default=True,
    )


def post_init_hook(env):
    env["repair.group.init"]._init_settings()


class RepairGroupInit(models.TransientModel):
    _name = "repair.group.init"
    _description = "Repair Group Init"

    @api.model
    def _init_settings(self):
        # with_user(SUPERUSER_ID) is required here because res.config.settings
        # restricts access to administrators. This method is only called from
        # the post_init_hook during module installation, so the elevated
        # privilege is intentional and limited in scope.
        settings = (
            self.env["res.config.settings"]
            .with_user(SUPERUSER_ID)
            .with_context(active_test=False, install_mode=True)
            .create({"group_stock_tracking_owner": True})
        )
        settings.execute()
        return True
