# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    duration_hours = fields.Float(
        string="Duration (Hours)",
        compute="_compute_duration_hours",
        help="Duration in hours. The native duration field stores minutes "
        "but the Time Tracking view displays it with the float_time "
        "widget, which expects hours, so it misrenders (e.g. 124 minutes "
        "shown as 124:00 instead of 2:04). This field converts to hours "
        "so the widget renders it correctly.",
    )

    @api.depends("duration")
    def _compute_duration_hours(self):
        for productivity in self:
            productivity.duration_hours = productivity.duration / 60.0
