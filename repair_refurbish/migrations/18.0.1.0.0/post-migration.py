# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # The new default has been created,
    # update it with what the user had set in the old `ir.property`
    env.cr.execute(
        """
SELECT value_reference
FROM ir_property ip
JOIN ir_model_fields imf ON imf.id = ip.fields_id
WHERE
    ip.name = 'property_stock_refurbish' AND imf.model = 'product.template'
    AND company_id IS NULL
        """
    )
    row = env.cr.fetchone()
    if property_default := row and row[0]:
        # The property was a reference value "model,ID"
        # but the value of the default is now only the location's ID
        _model, res_id = property_default.split(",")
        env.ref("repair_refurbish.property_stock_refurbish").json_value = json.dumps(
            int(res_id)
        )
