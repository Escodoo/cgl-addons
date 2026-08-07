# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        index=True,
        default=lambda self: self.env.user.employee_id,
        help="Employee who performed the activity, for labor cost "
        "attribution. Independent from the user that logged the record.",
    )
