# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class TimesheetsAnalysisReport(models.Model):
    _inherit = "timesheets.analysis.report"

    # repair_timesheet adds this column to account.analytic.line, but the
    # report is an _auto = False SQL view with a fixed column list, so the
    # field has to be declared and selected explicitly here.
    repair_order_id = fields.Many2one(
        "repair.order",
        string="Repair Order",
        readonly=True,
    )

    @api.model
    def _select(self):
        return super()._select() + ", A.repair_order_id AS repair_order_id"
