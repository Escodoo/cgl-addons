# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_obra_account(self):
        """Extract the 'Obra' analytic account carried on this move's
        analytic distribution, if any.
        """
        self.ensure_one()
        plan = self.company_id.obra_analytic_plan_id
        if not plan:
            return self.env["account.analytic.account"]
        root_plan = plan.root_id
        return self.distribution_analytic_account_ids.filtered(
            lambda a: a.root_plan_id == root_plan
        )[:1]
