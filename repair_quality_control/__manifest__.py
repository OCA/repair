# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Repair Quality Control",
    "summary": "Create quality controls from repair order",
    "version": "16.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Antoni Marroig, Odoo Community Association (OCA)",
    "maintainers": ["peluko00"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_repair_config",
        "quality_control_stock_oca",
    ],
    "data": [
        "data/repair_quality_control_data.xml",
        "views/res_config_settings_views.xml",
        "views/repair_views.xml",
        "views/qc_inspection_views.xml",
    ],
}
