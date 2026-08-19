from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    user_id = fields.Many2one(
        related="move_id.user_id",
        string="User",
        store=True,
        readonly=False,
    )
