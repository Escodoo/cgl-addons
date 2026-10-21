# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import models

EXTENSION_VIEW_NAME = "cgl.hour.appropriation.float_time"

# Decimal hours column of the "Relatório de Apropriação de Horas" SQL report.
HOURS_FIELD = "x_horas_decimal"
# Label used by the report's columns, which are written in Portuguese.
HOURS_LABEL = "Horas"
# Text column ("H:MM") of the same report. It cannot be summed, so it is
# replaced by HOURS_FIELD, which is shown as HH:MM through ``float_time``.
TEXT_HOURS_FIELD = "x_horas"


class BiSqlView(models.Model):
    _inherit = "bi.sql.view"

    def button_create_ui(self):
        res = super().button_create_ui()
        self._sync_float_time_views()
        return res

    def button_reset_to_model_valid(self):
        # ir.ui.view.inherit_id is ondelete="restrict", so the generated views
        # cannot be deleted while the extension views still point to them.
        self._unlink_float_time_views()
        return super().button_reset_to_model_valid()

    def _float_time_parent_views(self):
        self.ensure_one()
        return self.tree_view_id | self.pivot_view_id | self.graph_view_id

    def _has_float_time_field(self):
        self.ensure_one()
        return any(
            field.name == HOURS_FIELD and field.ttype == "float"
            for field in self.bi_sql_view_field_ids
        )

    def _find_float_time_views(self):
        parents = self.env["ir.ui.view"]
        for sql_view in self:
            parents |= sql_view._float_time_parent_views()
        return (
            self.env["ir.ui.view"]
            .with_context(active_test=False)
            .search(
                [
                    ("inherit_id", "in", parents.ids),
                    ("name", "=", EXTENSION_VIEW_NAME),
                ]
            )
        )

    def _unlink_float_time_views(self):
        self._find_float_time_views().unlink()

    def _float_time_arch(self, parent_view):
        """Arch extending a generated view so the hours are shown as HH:MM.

        Return False when the generated view does not show the hours column,
        so there is nothing to extend.
        """
        root = etree.fromstring(parent_view.arch.encode())
        names = {node.get("name") for node in root.iter("field")}
        if HOURS_FIELD not in names:
            return False
        xpaths = [
            f"""<xpath expr="//field[@name='{HOURS_FIELD}']" position="attributes">
                <attribute name="string">{HOURS_LABEL}</attribute>
                <attribute name="widget">float_time</attribute>
            </xpath>"""
        ]
        if parent_view.type == "list" and TEXT_HOURS_FIELD in names:
            xpaths.append(
                f"""<xpath expr="//field[@name='{TEXT_HOURS_FIELD}']"
                    position="attributes">
                    <attribute name="optional">hide</attribute>
                </xpath>"""
            )
        return f"<data>{''.join(xpaths)}</data>"

    def _sync_float_time_views(self):
        """Create, update or remove the extension of the generated views."""
        View = self.env["ir.ui.view"]
        for sql_view in self.filtered(
            lambda v: v.state == "ui_valid" and v._has_float_time_field()
        ):
            for parent_view in sql_view._float_time_parent_views():
                arch = sql_view._float_time_arch(parent_view)
                extension = sql_view._find_float_time_views().filtered(
                    lambda v, parent_view=parent_view: v.inherit_id == parent_view
                )
                if arch and extension:
                    extension.arch = arch
                elif arch:
                    View.create(
                        {
                            "name": EXTENSION_VIEW_NAME,
                            "model": parent_view.model,
                            "inherit_id": parent_view.id,
                            "mode": "extension",
                            "arch": arch,
                        }
                    )
                else:
                    extension.unlink()
