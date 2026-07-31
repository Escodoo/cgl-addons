# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests.common import TransactionCase


class TestCglRepairOrderCustom(TransactionCase):
    def test_picked_column_hidden_in_repair_order_parts(self):
        """The 'picked' (Usado) column is hidden in the Repair Order's
        Parts tab, without touching the field definition itself."""
        view = self.env["repair.order"].get_view(
            view_id=self.env.ref("repair.view_repair_order_form").id,
            view_type="form",
        )
        arch = etree.fromstring(view["arch"])
        picked_fields = arch.xpath("//field[@name='move_ids']//field[@name='picked']")
        self.assertTrue(picked_fields, "picked field not found in the Parts list.")
        self.assertEqual(picked_fields[0].get("column_invisible"), "1")

    def test_picked_field_still_exists_on_stock_move(self):
        """The stock.move model field itself is untouched by this module."""
        self.assertIn("picked", self.env["stock.move"]._fields)
