# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    show_register_obra_scrap = fields.Boolean(
        compute="_compute_show_register_obra_scrap",
        help="Transferência partindo do local de materiais em obra, com "
        "quantidade ainda pendente de retorno.",
    )

    def _get_pending_obra_moves(self):
        """Moves of this picking that still owe a return: not yet done/
        cancelled, with demand left to fulfill."""
        return self.move_ids.filtered(
            lambda m: m.state not in ("done", "cancel") and m.product_uom_qty > 0
        )

    def _compute_show_register_obra_scrap(self):
        obra_location = self.env["stock.scrap"]._get_obra_stock_location()
        for picking in self:
            picking.show_register_obra_scrap = bool(
                obra_location
                and picking.location_id == obra_location
                and picking._get_pending_obra_moves()
            )

    def action_register_obra_scrap(self):
        """Pre-fill one draft `stock.scrap` per pending line of this
        transfer (product, quantity still not returned, obra), so the user
        only has to pick the reason and write the justification instead of
        re-entering everything by hand.
        """
        self.ensure_one()
        obra_location = self.env["stock.scrap"]._get_obra_stock_location()
        if not obra_location:
            raise UserError(_("Local de materiais em obra não configurado."))

        pending_moves = self._get_pending_obra_moves()
        if not pending_moves:
            raise UserError(
                _("Não há quantidade pendente para dar baixa nesta " "transferência.")
            )

        # The pending move itself is only cancelled once its scrap is
        # actually validated (see StockScrap.action_validate) - not here -
        # so an abandoned draft scrap doesn't silently drop the pending
        # quantity from tracking.
        scraps = self.env["stock.scrap"].create(
            [
                {
                    "product_id": move.product_id.id,
                    "product_uom_id": move.product_uom.id,
                    "scrap_qty": move.product_uom_qty,
                    "location_id": obra_location.id,
                    "picking_id": self.id,
                    "move_id": move.id,
                    "obra_id": move._get_obra_account().id,
                }
                for move in pending_moves
            ]
        )

        action = {
            "type": "ir.actions.act_window",
            "name": _("Baixa de Material Não Retornado"),
            "res_model": "stock.scrap",
            "domain": [("id", "in", scraps.ids)],
        }
        if len(scraps) == 1:
            action.update({"view_mode": "form", "res_id": scraps.id})
        else:
            action["view_mode"] = "list,form"
        return action
