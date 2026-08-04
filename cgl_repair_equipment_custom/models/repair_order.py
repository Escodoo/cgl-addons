from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    equipment_id = fields.Many2one(
        comodel_name="maintenance.equipment",
        string="Equipment",
        check_company=True,
    )

    @api.constrains("product_id", "equipment_id")
    def _check_product_or_equipment(self):
        for repair in self:
            if not repair.product_id and not repair.equipment_id:
                raise ValidationError(
                    _("A Repair Order must be linked to a Product or an Equipment.")
                )
