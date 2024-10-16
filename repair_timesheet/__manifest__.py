# Copyright 2024 Patryk Pyczko (APSL-Nagarro)<ppyczko@apsl.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Timesheet",
    "version": "17.0.1.0.0",
    "category": "Repair",
    "website": "https://github.com/OCA/repair",
    "author": "APSL-Nagarro, Odoo Community Association (OCA)",
    "maintainers": ["ppyczko"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["repair", "hr_timesheet"],
    "data": ["views/repair_views.xml"],
}
