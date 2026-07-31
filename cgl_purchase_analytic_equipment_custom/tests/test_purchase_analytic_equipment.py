# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestPurchaseAnalyticEquipment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.equipment_account = cls.env.ref(
            "cgl_purchase_analytic_equipment_custom."
            "analytic_account_equipamentos_escavadeira"
        )
        cls.equipment_account_2 = cls.env.ref(
            "cgl_purchase_analytic_equipment_custom."
            "analytic_account_equipamentos_retroescavadeira"
        )

        cls.project_plan = cls.env.ref("analytic.analytic_plan_projects")
        cls.project_account = cls.env["account.analytic.account"].create(
            {"name": "Test Project Account", "plan_id": cls.project_plan.id}
        )

        cls.partner = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test Product 1", "type": "consu"}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "type": "consu"}
        )

    def _make_order(self, equipment_cost_center_id=False):
        return self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "equipment_cost_center_id": equipment_cost_center_id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_1.id,
                            "product_qty": 1.0,
                            "price_unit": 10.0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product_2.id,
                            "product_qty": 1.0,
                            "price_unit": 20.0,
                        }
                    ),
                ],
            }
        )

    def test_equipment_cost_center_applies_to_all_lines(self):
        """Setting the header field applies it to every existing line."""
        order = self._make_order(equipment_cost_center_id=self.equipment_account.id)

        for line in order.order_line:
            self.assertEqual(
                line.analytic_distribution,
                {str(self.equipment_account.id): 100.0},
            )

    def test_no_equipment_cost_center_no_changes(self):
        """Without the header field set, line distributions are untouched."""
        order = self._make_order()

        for line in order.order_line:
            self.assertFalse(line.analytic_distribution)

    def test_equipment_cost_center_preserves_other_plan_accounts(self):
        """Applying the equipment account keeps an existing Projeto account
        on the same line instead of overwriting it."""
        order = self._make_order()
        order.order_line[0].analytic_distribution = {
            str(self.project_account.id): 100.0
        }

        order.equipment_cost_center_id = self.equipment_account.id

        distribution = order.order_line[0].analytic_distribution
        self.assertEqual(len(distribution), 1)
        ((key, percentage),) = distribution.items()
        ids = {int(part) for part in key.split(",")}
        self.assertEqual(ids, {self.project_account.id, self.equipment_account.id})
        self.assertEqual(percentage, 100.0)

    def test_equipment_cost_center_replaces_previous_equipment_account(self):
        """Changing the header field to a different equipment account
        replaces the old one on the lines rather than duplicating it."""
        order = self._make_order(equipment_cost_center_id=self.equipment_account.id)

        order.equipment_cost_center_id = self.equipment_account_2.id

        for line in order.order_line:
            self.assertEqual(
                line.analytic_distribution,
                {str(self.equipment_account_2.id): 100.0},
            )

    def test_individual_line_edit_is_not_overridden(self):
        """A manual edit to one line's distribution, made after the header
        cascade, is not reverted by further unrelated writes to the order."""
        order = self._make_order(equipment_cost_center_id=self.equipment_account.id)

        order.order_line[0].analytic_distribution = {
            str(self.project_account.id): 100.0
        }
        # Trigger an unrelated write on the order; must not re-cascade.
        order.write({"partner_ref": "PO-REF-1"})

        self.assertEqual(
            order.order_line[0].analytic_distribution,
            {str(self.project_account.id): 100.0},
        )

    def test_new_line_inherits_equipment_cost_center(self):
        """A line added after the header field is already set also gets
        the equipment account applied on creation."""
        order = self._make_order(equipment_cost_center_id=self.equipment_account.id)

        new_line = self.env["purchase.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product_1.id,
                "product_qty": 1.0,
                "price_unit": 5.0,
            }
        )

        self.assertEqual(
            new_line.analytic_distribution,
            {str(self.equipment_account.id): 100.0},
        )
