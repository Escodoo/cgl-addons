# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

EQUIPMENT_PLAN_XMLID = (
    "cgl_purchase_analytic_equipment_custom.analytic_plan_equipamentos"
)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _get_equipment_plan(self):
        """Resolve the Equipment plan by XML ID.

        Never look it up by name: `account.analytic.plan.name` is a
        translated (jsonb) field, so a name-based domain resolves against
        the current user's language and breaks on rename, case, accent or
        trailing whitespace.
        """
        return self.env.ref(EQUIPMENT_PLAN_XMLID, raise_if_not_found=False)

    @api.model
    def _get_equipment_cost_center_domain(self):
        plan = self._get_equipment_plan()
        if not plan:
            return [("id", "=", False)]
        # child_of so accounts under sub-plans of Equipamentos are included.
        return [("plan_id", "child_of", plan.id)]

    equipment_cost_center_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Centro de Custo (Equipamentos)",
        domain=lambda self: self._get_equipment_cost_center_domain(),
        check_company=True,
        help="Automatically applied to every order line's analytic "
        "distribution. Each line remains individually editable "
        "afterwards.",
    )

    def _cascade_equipment_cost_center(self):
        """Push the header value down to the lines.

        Also runs when the field is cleared, so that emptying it removes the
        Equipment account from the lines instead of stranding it there.
        """
        for order in self:
            plan = order._get_equipment_plan()
            if not plan:
                continue
            order.order_line._apply_equipment_cost_center(
                order.equipment_cost_center_id, plan
            )

    @api.onchange("equipment_cost_center_id")
    def _onchange_equipment_cost_center_id(self):
        self._cascade_equipment_cost_center()

    def write(self, vals):
        res = super().write(vals)
        if "equipment_cost_center_id" in vals:
            self._cascade_equipment_cost_center()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders.filtered("equipment_cost_center_id")._cascade_equipment_cost_center()
        return orders
