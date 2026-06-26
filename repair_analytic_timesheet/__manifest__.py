# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Analytic Timesheet",
    "summary": "Spreads timesheet costs through analytic distribution on repair orders",
    "version": "18.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["repair_analytic", "repair_timesheet"],
    "data": [
        "views/project_project_views.xml",
    ],
}
