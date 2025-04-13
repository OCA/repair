# Copyright 2025 Vicent Cubells - Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class RepairOrder(models.Model):
    _name = "repair.order"
    _inherit = ["repair.order", "comment.template"]
