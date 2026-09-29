# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Repair picking after done",
    "version": "18.0.1.0.1",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "summary": "Transfer repaired move to another location directly from repair order",
    "category": "Repair",
    "depends": [
        "base_repair_config",
        "repair_type",
        "repair_stock",
        "repair_type_product_destination",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/repair.xml",
        "views/res_config_settings_views.xml",
        "wizards/repair_move_transfer_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "license": "AGPL-3",
    "application": False,
    "post_load": "post_load_hook",
}
