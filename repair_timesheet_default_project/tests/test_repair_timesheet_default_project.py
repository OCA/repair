# Copyright 2026 Escodoo - Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestRepairTimesheetDefaultProject(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.project = cls.env["project.project"].create(
            {
                "name": "Test Repair Timesheets Project",
                "allow_timesheets": True,
                "billing_type": "not_billable",
            }
        )
        cls.task = cls.env["project.task"].create(
            {"name": "Test Repair Timesheets Task", "project_id": cls.project.id}
        )

    def test_settings_store_defaults_on_company(self):
        settings = self.env["res.config.settings"].create(
            {
                "repair_timesheet_default_project_id": self.project.id,
                "repair_timesheet_default_task_id": self.task.id,
            }
        )
        settings.execute()

        self.assertEqual(
            self.env.company.repair_timesheet_default_project_id, self.project
        )
        self.assertEqual(self.env.company.repair_timesheet_default_task_id, self.task)

    def test_repair_order_exposes_company_defaults(self):
        self.env.company.write(
            {
                "repair_timesheet_default_project_id": self.project.id,
                "repair_timesheet_default_task_id": self.task.id,
            }
        )
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        repair = self.env["repair.order"].create(
            {"picking_type_id": warehouse.repair_type_id.id}
        )

        self.assertEqual(repair.repair_timesheet_default_project_id, self.project)
        self.assertEqual(repair.repair_timesheet_default_task_id, self.task)
