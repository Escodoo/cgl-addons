from odoo.tests.common import TransactionCase


class TestRepairTimesheetReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {"name": "Test Product To Repair", "type": "consu"}
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.repair_type = cls.warehouse.repair_type_id
        cls.employee = cls.env["hr.employee"].create({"name": "Test Technician"})
        cls.project = cls.env["project.project"].create({"name": "Test Project"})

        cls.repair = cls.env["repair.order"].create(
            {
                "product_id": cls.product.id,
                "picking_type_id": cls.repair_type.id,
            }
        )
        cls.timesheet = cls.env["account.analytic.line"].create(
            {
                "name": "Fixed the pump",
                "repair_order_id": cls.repair.id,
                "project_id": cls.project.id,
                "employee_id": cls.employee.id,
                "unit_amount": 2.5,
                "company_id": cls.repair.company_id.id,
            }
        )

    def test_report_line_created_for_repair_timesheet(self):
        report_line = self.env["timesheets.analysis.report"].search(
            [("repair_order_id", "=", self.repair.id)]
        )
        self.assertEqual(len(report_line), 1)
        self.assertEqual(report_line.employee_id, self.employee)
        self.assertEqual(report_line.unit_amount, 2.5)
        self.assertEqual(report_line.name, "Fixed the pump")

    def test_report_excludes_non_repair_timesheets(self):
        self.env["account.analytic.line"].create(
            {
                "name": "Unrelated work",
                "project_id": self.project.id,
                "employee_id": self.employee.id,
                "unit_amount": 1.0,
                "company_id": self.env.company.id,
            }
        )
        repair_report_lines = self.env["timesheets.analysis.report"].search(
            [("employee_id", "=", self.employee.id), ("repair_order_id", "!=", False)]
        )
        self.assertEqual(len(repair_report_lines), 1)
        self.assertEqual(repair_report_lines.repair_order_id, self.repair)

    def test_action_domain_and_views_render(self):
        action = self.env.ref(
            "cgl_repair_timesheet_report_custom."
            "action_repair_timesheets_analysis_report"
        )
        self.assertEqual(action.domain, "[('repair_order_id', '!=', False)]")

        for view_xmlid, view_type in [
            ("repair_timesheets_analysis_report_list", "list"),
            ("repair_timesheets_analysis_report_pivot", "pivot"),
            ("repair_timesheets_analysis_report_search", "search"),
        ]:
            view = self.env.ref(f"cgl_repair_timesheet_report_custom.{view_xmlid}")
            self.env["timesheets.analysis.report"].get_view(
                view_id=view.id, view_type=view_type
            )
