# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Repair Notification",
    "summary": """Send mail notifications to the customer to inform about repair start/end""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/repair",
    "depends": ["base_repair_config", "repair"],
    "data": [
        "views/res_config_settings.xml",
        "data/mail_data.xml",
    ],
}
