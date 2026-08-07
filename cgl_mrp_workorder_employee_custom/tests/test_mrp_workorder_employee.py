# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestMrpWorkorderEmployee(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Test Operator",
                "login": "test_operator",
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Operator",
                "user_id": cls.user.id,
            }
        )

    def test_employee_defaults_from_logged_user(self):
        defaults = (
            self.env["mrp.workcenter.productivity"]
            .with_user(self.user)
            .default_get(["employee_id"])
        )
        self.assertEqual(defaults.get("employee_id"), self.employee.id)

    def test_employee_empty_when_user_has_no_employee(self):
        user_without_employee = self.env["res.users"].create(
            {
                "name": "No Employee User",
                "login": "no_employee_user",
            }
        )
        defaults = (
            self.env["mrp.workcenter.productivity"]
            .with_user(user_without_employee)
            .default_get(["employee_id"])
        )
        self.assertFalse(defaults.get("employee_id"))

    def test_employee_can_be_set_explicitly(self):
        other_employee = self.env["hr.employee"].create({"name": "Other Employee"})
        workcenter = self.env["mrp.workcenter"].create({"name": "Test Workcenter"})
        productivity = self.env["mrp.workcenter.productivity"].create(
            {
                "workcenter_id": workcenter.id,
                "loss_id": self.env.ref("mrp.block_reason0").id,
                "employee_id": other_employee.id,
            }
        )
        self.assertEqual(productivity.employee_id, other_employee)
