# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _apply_equipment_cost_center(self, account, plan):
        """Merge `account` into each line's analytic_distribution.

        Replaces any account belonging to `plan` while preserving accounts
        from other plans (e.g. Projeto) and existing percentage splits.
        An empty `account` removes the plan's accounts from the lines.
        """
        root_plan = plan.root_id
        for line in self:
            new_distribution = line._merge_analytic_account(
                line.analytic_distribution, account, root_plan
            )
            if new_distribution != (line.analytic_distribution or {}):
                line.analytic_distribution = new_distribution or False

    @api.model
    def _merge_analytic_account(self, distribution, account, root_plan):
        if not distribution:
            return {str(account.id): 100.0} if account else {}
        analytic_account = self.env["account.analytic.account"]
        new_distribution = {}
        for key, percentage in distribution.items():
            ids = [int(part) for part in key.split(",") if part.strip().isdigit()]
            # Drop accounts of the target plan; keep every other plan's.
            kept = (
                analytic_account.browse(ids)
                .exists()
                .filtered(lambda a: a.root_plan_id != root_plan)
                .ids
            )
            if account:
                kept.append(account.id)
            if not kept:
                continue
            new_key = ",".join(str(i) for i in sorted(set(kept)))
            # Accumulate: two keys can collapse into the same one once the
            # plan's accounts are stripped, and the percentages must add up
            # instead of overwriting each other.
            new_distribution[new_key] = new_distribution.get(new_key, 0.0) + percentage
        return new_distribution

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for order, order_lines in lines.grouped("order_id").items():
            if order.equipment_cost_center_id:
                plan = order._get_equipment_plan()
                if plan:
                    order_lines._apply_equipment_cost_center(
                        order.equipment_cost_center_id, plan
                    )
        return lines
