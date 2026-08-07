# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command
from odoo.tests.common import TransactionCase


class TestPurchaseAnalyticEquipment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.analytic_account = cls.env["account.analytic.account"]
        cls.equipment_plan = cls.env.ref(
            "cgl_purchase_analytic_equipment_custom.analytic_plan_equipamentos"
        )

        # Created here rather than pulled from demo data, so the suite is
        # meaningful on a database installed with --without-demo.
        cls.equipment_account = cls.analytic_account.create(
            {"name": "03 - ESCAVADEIRA", "plan_id": cls.equipment_plan.id}
        )
        cls.equipment_account_2 = cls.analytic_account.create(
            {"name": "04 - RETROESCAVADEIRA", "plan_id": cls.equipment_plan.id}
        )
        cls.equipment_account_3 = cls.analytic_account.create(
            {"name": "05 - PERFURATRIZ", "plan_id": cls.equipment_plan.id}
        )

        cls.project_plan = cls.env.ref("analytic.analytic_plan_projects")
        cls.project_account = cls.analytic_account.create(
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

    def _cost_center_selection(self):
        domain = self.env["purchase.order"]._get_equipment_cost_center_domain()
        return self.analytic_account.search(domain)

    # -- domain -----------------------------------------------------------

    def test_domain_lists_only_equipment_plan_accounts(self):
        """The selectable cost centers are the Equipment plan's, and only
        those."""
        accounts = self._cost_center_selection()

        self.assertIn(self.equipment_account, accounts)
        self.assertIn(self.equipment_account_2, accounts)
        self.assertNotIn(self.project_account, accounts)

    def test_domain_survives_plan_rename(self):
        """Regression: the domain used to match on `plan_id.name`, which is a
        translated (jsonb) field. Renaming or translating the plan emptied the
        dropdown. The plan is now resolved by XML ID."""
        self.equipment_plan.name = "Equipamentos Pesados 2026"

        self.assertIn(self.equipment_account, self._cost_center_selection())

    def test_domain_includes_sub_plan_accounts(self):
        """Accounts under a sub-plan of Equipment are selectable too."""
        sub_account = self._make_sub_plan_account()

        self.assertIn(sub_account, self._cost_center_selection())

    def _make_sub_plan_account(self):
        sub_plan = self.env["account.analytic.plan"].create(
            {"name": "Escavadeiras", "parent_id": self.equipment_plan.id}
        )
        return self.analytic_account.create(
            {"name": "03.1 - ESCAVADEIRA CAT", "plan_id": sub_plan.id}
        )

    # -- cascade to lines -------------------------------------------------

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

    def test_split_between_equipment_accounts_keeps_total(self):
        """Regression: a line split across two Equipment accounts used to
        collapse into a single key, and the last percentage overwrote the
        first one -- a 60/40 split became a lone 40%, silently dropping 60
        points off the distribution."""
        order = self._make_order()
        line = order.order_line[0]
        line.analytic_distribution = {
            str(self.equipment_account.id): 60.0,
            str(self.equipment_account_2.id): 40.0,
        }

        order.equipment_cost_center_id = self.equipment_account_3.id

        self.assertEqual(
            line.analytic_distribution,
            {str(self.equipment_account_3.id): 100.0},
        )

    def test_sub_plan_account_is_replaced(self):
        """Regression: replacement matched on the exact plan, so an account
        sitting in a sub-plan of Equipment survived and the line ended up
        carrying two equipment cost centers."""
        sub_account = self._make_sub_plan_account()
        order = self._make_order()
        order.order_line[0].analytic_distribution = {str(sub_account.id): 100.0}

        order.equipment_cost_center_id = self.equipment_account.id

        self.assertEqual(
            order.order_line[0].analytic_distribution,
            {str(self.equipment_account.id): 100.0},
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

    def test_onchange_cascades_before_the_order_is_saved(self):
        """The form applies the cost center as soon as it is picked, not only
        on save. Exercises the onchange path, which create/write tests skip."""
        order = self.env["purchase.order"].new(
            {
                "partner_id": self.partner.id,
                "equipment_cost_center_id": self.equipment_account.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_1.id,
                            "product_qty": 1.0,
                            "price_unit": 10.0,
                        }
                    )
                ],
            }
        )

        order._onchange_equipment_cost_center_id()

        self.assertEqual(
            order.order_line.analytic_distribution,
            {str(self.equipment_account.id): 100.0},
        )

    # -- missing plan -----------------------------------------------------

    def test_missing_plan_degrades_gracefully(self):
        """If the plan record is deleted, the field offers nothing and the
        cascade is skipped, rather than raising on every order write."""
        purchase_order = self.env["purchase.order"]
        with patch.object(
            type(purchase_order),
            "_get_equipment_plan",
            return_value=self.env["account.analytic.plan"],
        ):
            self.assertFalse(self._cost_center_selection())

            order = self._make_order(equipment_cost_center_id=self.equipment_account.id)

            for line in order.order_line:
                self.assertFalse(line.analytic_distribution)

    # -- clearing the header ----------------------------------------------

    def test_clearing_header_removes_account_from_lines(self):
        """Emptying the header field pulls the equipment account back off the
        lines instead of stranding it there."""
        order = self._make_order(equipment_cost_center_id=self.equipment_account.id)

        order.equipment_cost_center_id = False

        for line in order.order_line:
            self.assertFalse(line.analytic_distribution)

    def test_clearing_header_preserves_other_plan_accounts(self):
        """Clearing only removes the Equipment plan's account; a Projeto
        account on the same line stays."""
        order = self._make_order()
        order.order_line[0].analytic_distribution = {
            str(self.project_account.id): 100.0
        }
        order.equipment_cost_center_id = self.equipment_account.id

        order.equipment_cost_center_id = False

        self.assertEqual(
            order.order_line[0].analytic_distribution,
            {str(self.project_account.id): 100.0},
        )
