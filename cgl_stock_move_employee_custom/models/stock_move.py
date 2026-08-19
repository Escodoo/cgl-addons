from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        check_company=True,
        help="User performing this stock withdrawal.",
    )
