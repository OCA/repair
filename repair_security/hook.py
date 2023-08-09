from odoo import SUPERUSER_ID
from odoo.api import Environment


def post_init_hook(cr, _):
    env = Environment(cr, SUPERUSER_ID, {})
    # Giving Repair Admin access to match the previous permissions.
    env.ref("repair_security.group_repair_manager").write(
        {
            "users": [(6, 0, env.ref("stock.group_stock_user").users.ids)],
        }
    )
