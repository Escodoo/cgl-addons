# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    obra_stock_location_id = fields.Many2one(
        related="company_id.obra_stock_location_id", readonly=False
    )
    obra_analytic_plan_id = fields.Many2one(
        related="company_id.obra_analytic_plan_id", readonly=False
    )

    def set_values(self):
        res = super().set_values()
        self.company_id._setup_obra_picking_types()
        return res
