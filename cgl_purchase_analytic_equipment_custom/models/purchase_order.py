# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    equipment_cost_center_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Centro de Custo (Equipamentos)",
        domain="[('plan_id.name', '=', 'Equipamentos')]",
        help="Automatically applied to every order line's analytic "
        "distribution. Each line remains individually editable "
        "afterwards.",
    )

    @api.onchange("equipment_cost_center_id")
    def _onchange_equipment_cost_center_id(self):
        if self.equipment_cost_center_id:
            self.order_line._apply_equipment_cost_center(self.equipment_cost_center_id)

    def write(self, vals):
        res = super().write(vals)
        if "equipment_cost_center_id" in vals:
            for order in self:
                if order.equipment_cost_center_id:
                    order.order_line._apply_equipment_cost_center(
                        order.equipment_cost_center_id
                    )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.equipment_cost_center_id:
                order.order_line._apply_equipment_cost_center(
                    order.equipment_cost_center_id
                )
        return orders
