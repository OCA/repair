# Copyright 2024 Antoni Marroig(APSL-Nagarro)<amarroig@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Repair Quality Control",
    "summary": "Create quality controls from repair order",
    "version": "17.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Antoni Marroig, Odoo Community Association (OCA)",
    "maintainers": ["peluko00"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "repair",
        "quality_control_stock_oca",
    ],
    "data": [
        "views/repair_views.xml",
        "views/qc_inspection_views.xml",
    ],
}
