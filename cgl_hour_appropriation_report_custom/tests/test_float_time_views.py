# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import importlib.util
from itertools import count
from pathlib import Path

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import SingleTransactionCase

from odoo.addons.cgl_hour_appropriation_report_custom import (
    post_init_hook,
    uninstall_hook,
)
from odoo.addons.cgl_hour_appropriation_report_custom.models.bi_sql_view import (
    EXTENSION_VIEW_NAME,
)


class _Rollback(Exception):
    """Raised to undo the savepoint of a test."""


# Same columns as the "Relatório de Apropriação de Horas" SQL report.
HOURS_QUERY = """
SELECT
    'Teste'::varchar AS x_origem,
    name::varchar AS x_documento,
    ROUND(1.5::numeric, 2) AS x_horas_decimal,
    90::integer AS x_minutos,
    '1:30'::varchar AS x_horas
FROM res_partner
"""
OTHER_QUERY = """
SELECT
    name::varchar AS x_documento,
    90::integer AS x_minutos
FROM res_partner
"""


# The models of the SQL views are created on the fly and do not survive the
# rollback of a TransactionCase, so, like bi_sql_editor, share one transaction.
@tagged("post_install", "-at_install")
class TestFloatTimeViews(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._counter = count()

    def _create_sql_view(self, query=HOURS_QUERY):
        technical_name = f"test_hours_report_{next(self._counter)}"
        sql_view = self.env["bi.sql.view"].create(
            {
                "name": f"Test {technical_name}",
                "technical_name": technical_name,
                "is_materialized": False,
                "query": query,
            }
        )
        sql_view.button_validate_sql_expression()
        sql_view.button_create_sql_view_and_model()
        return sql_view

    def _create_ui(self, sql_view, tree_visibility=None):
        hours = sql_view.bi_sql_view_field_ids.filtered(
            lambda f: f.name == "x_horas_decimal"
        )
        hours.graph_type = "measure"
        if tree_visibility:
            hours.tree_visibility = tree_visibility
        sql_view.button_create_ui()

    def _field_node(self, sql_view, parent_view, name):
        arch = self.env[sql_view.model_id.model].get_view(
            view_id=parent_view.id, view_type=parent_view.type
        )["arch"]
        nodes = etree.fromstring(arch).xpath(f"//field[@name='{name}']")
        return nodes[0] if nodes else None

    def test_generated_views_show_hours_as_float_time(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        views = {
            "list": sql_view.tree_view_id,
            "pivot": sql_view.pivot_view_id,
            "graph": sql_view.graph_view_id,
        }
        self.assertEqual(len(sql_view._find_float_time_views()), 3)
        for view_type, view in views.items():
            node = self._field_node(sql_view, view, "x_horas_decimal")
            self.assertEqual(node.get("widget"), "float_time", view_type)
            self.assertEqual(node.get("string"), "Horas", view_type)

    def test_text_hours_column_is_hidden_in_list_only(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        node = self._field_node(sql_view, sql_view.tree_view_id, "x_horas")
        self.assertEqual(node.get("optional"), "hide")
        node = self._field_node(sql_view, sql_view.pivot_view_id, "x_horas")
        self.assertIsNone(node.get("optional"))

    def test_other_columns_are_untouched(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        node = self._field_node(sql_view, sql_view.tree_view_id, "x_minutos")
        self.assertIsNone(node.get("widget"))
        self.assertIsNone(node.get("string"))

    def test_sync_is_idempotent(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        extensions = sql_view._find_float_time_views()
        sql_view._sync_float_time_views()
        sql_view._sync_float_time_views()
        self.assertEqual(sql_view._find_float_time_views(), extensions)

    def test_delete_ui_then_create_ui_again(self):
        """The generated views are restricted by their extensions on delete."""
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        self.assertTrue(sql_view._find_float_time_views())
        sql_view.button_reset_to_model_valid()
        self.assertEqual(sql_view.state, "model_valid")
        self.assertFalse(sql_view._find_float_time_views())
        self._create_ui(sql_view)
        self.assertEqual(len(sql_view._find_float_time_views()), 3)

    def test_set_draft(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        sql_view.button_set_draft()
        self.assertEqual(sql_view.state, "draft")
        self.assertFalse(sql_view._find_float_time_views())

    def test_hours_not_shown_in_the_list(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view, tree_visibility="unavailable")
        extensions = sql_view._find_float_time_views()
        self.assertNotIn(sql_view.tree_view_id, extensions.inherit_id)
        self.assertEqual(len(extensions), 2)
        # The text column must stay visible if there is no column to replace it.
        node = self._field_node(sql_view, sql_view.tree_view_id, "x_horas")
        self.assertIsNone(node.get("optional"))

    def test_report_without_hours_field_is_ignored(self):
        sql_view = self._create_sql_view(OTHER_QUERY)
        sql_view.button_create_ui()
        self.assertFalse(sql_view._find_float_time_views())

    def test_post_init_hook_extends_existing_ui(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        sql_view._find_float_time_views().unlink()
        post_init_hook(self.env)
        self.assertEqual(len(sql_view._find_float_time_views()), 3)

    def test_uninstall_hook_removes_extensions(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        extensions = sql_view._find_float_time_views()
        # Archived extensions are removed too.
        extensions[:1].active = False
        # The hook removes the extensions of every report, and the transaction
        # is shared by the tests: roll it back to not depend on the test order.
        with self.assertRaises(_Rollback), self.env.cr.savepoint():
            uninstall_hook(self.env)
            self.assertFalse(sql_view._find_float_time_views())
            self.assertFalse(
                self.env["ir.ui.view"]
                .with_context(active_test=False)
                .search([("name", "=", EXTENSION_VIEW_NAME)])
            )
            self.assertTrue(sql_view.tree_view_id)
            raise _Rollback()
        self.env.invalidate_all()
        self.assertEqual(len(sql_view._find_float_time_views()), 3)

    def test_migration_refreshes_extensions(self):
        sql_view = self._create_sql_view()
        self._create_ui(sql_view)
        extension = sql_view._find_float_time_views()[:1]
        extension.arch = "<data/>"
        path = Path(__file__).parent.parent / "migrations/18.0.1.0.1/post-migration.py"
        spec = importlib.util.spec_from_file_location("post_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "18.0.1.0.0")
        self.env.invalidate_all()
        self.assertIn("float_time", extension.arch)
