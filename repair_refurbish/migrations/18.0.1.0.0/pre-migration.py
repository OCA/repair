# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Remove the old XMLID for the default value (not the record)
    # because it was a `ir.property`
    env["ir.model.data"].search(
        [
            ("module", "=", "repair_refurbish"),
            ("name", "=", "property_stock_refurbish"),
        ]
    ).unlink()
