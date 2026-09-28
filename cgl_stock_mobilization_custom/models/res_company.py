# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    obra_stock_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Local de Materiais em Obra",
        domain="[('usage', 'in', ('internal', 'transit'))]",
        help="Local intermediário que representa o material que está fora "
        "da CGL, em obras. Usado como origem/destino dos tipos de operação "
        "'Mobilização' e 'Desmobilização'.",
    )
    obra_analytic_plan_id = fields.Many2one(
        comodel_name="account.analytic.plan",
        string="Plano Analítico de Obras",
        help="Plano analítico (ex: 'Projeto') cujas contas identificam a "
        "obra em cada movimentação de mobilização, desmobilização e baixa.",
    )

    def _setup_obra_picking_types(self):
        """Create (or, if they already exist, re-point) the 'Mobilização'/
        'Desmobilização' picking types for this company's warehouse, based
        on the currently configured `obra_stock_location_id`.

        Called whenever the Inventory settings are saved, so changing the
        configured location later keeps both picking types in sync instead
        of requiring a reinstall.
        """
        self.ensure_one()
        if not self.obra_stock_location_id:
            return

        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.id)], limit=1
        )
        if not warehouse:
            return

        wh_stock_location = warehouse.lot_stock_id
        picking_type = self.env["stock.picking.type"]
        common_vals = {
            "code": "internal",
            "warehouse_id": warehouse.id,
            "company_id": self.id,
        }

        mob_type = picking_type.search(
            [
                ("sequence_code", "=", "MOB"),
                ("warehouse_id", "=", warehouse.id),
                ("code", "=", "internal"),
            ],
            limit=1,
        )
        mob_vals = {
            "name": "Mobilização",
            "sequence_code": "MOB",
            "default_location_src_id": wh_stock_location.id,
            "default_location_dest_id": self.obra_stock_location_id.id,
            **common_vals,
        }
        if mob_type:
            mob_type.write(mob_vals)
        else:
            mob_type = picking_type.create(mob_vals)

        desmob_type = picking_type.search(
            [
                ("sequence_code", "=", "DESMOB"),
                ("warehouse_id", "=", warehouse.id),
                ("code", "=", "internal"),
            ],
            limit=1,
        )
        desmob_vals = {
            "name": "Desmobilização",
            "sequence_code": "DESMOB",
            "default_location_src_id": self.obra_stock_location_id.id,
            "default_location_dest_id": wh_stock_location.id,
            **common_vals,
        }
        if desmob_type:
            desmob_type.write(desmob_vals)
        else:
            desmob_type = picking_type.create(desmob_vals)

        mob_type.return_picking_type_id = desmob_type.id
        desmob_type.return_picking_type_id = mob_type.id
