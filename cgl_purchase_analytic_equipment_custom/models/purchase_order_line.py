# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _apply_equipment_cost_center(self, account):
        """Merge `account` into each line's analytic_distribution.

        Replaces any existing account from the same analytic plan while
        preserving accounts from other plans (e.g. Projeto) and existing
        percentage splits.
        """
        plan_account_ids = (
            self.env["account.analytic.account"]
            .search([("plan_id", "=", account.plan_id.id)])
            .ids
        )
        for line in self:
            new_distribution = line._merge_analytic_account(
                line.analytic_distribution, account, plan_account_ids
            )
            if new_distribution != (line.analytic_distribution or {}):
                line.analytic_distribution = new_distribution

    @api.model
    def _merge_analytic_account(self, distribution, account, plan_account_ids):
        if not distribution:
            return {str(account.id): 100.0}
        new_distribution = {}
        for key, percentage in distribution.items():
            ids = [
                int(part)
                for part in key.split(",")
                if part.strip().isdigit() and int(part) not in plan_account_ids
            ]
            ids.append(account.id)
            new_key = ",".join(str(i) for i in sorted(set(ids)))
            new_distribution[new_key] = percentage
        return new_distribution

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.order_id.equipment_cost_center_id:
                line._apply_equipment_cost_center(
                    line.order_id.equipment_cost_center_id
                )
        return lines
