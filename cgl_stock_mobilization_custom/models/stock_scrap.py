# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    @api.model
    def _get_obra_plan(self):
        return self.env.company.obra_analytic_plan_id

    @api.model
    def _get_obra_stock_location(self):
        return self.env.company.obra_stock_location_id

    @api.model
    def _get_obra_domain(self):
        plan = self._get_obra_plan()
        if not plan:
            return [("id", "=", False)]
        return [("plan_id", "child_of", plan.id)]

    obra_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Obra",
        domain=lambda self: self._get_obra_domain(),
        check_company=True,
        help="Obra à qual esta baixa de material se refere. Aplicada "
        "automaticamente à distribuição analítica do registro.",
    )
    justificativa = fields.Text(
        help="Detalhamento do ocorrido (ex: data, local, boletim de " "ocorrência).",
    )
    is_obra_scrap = fields.Boolean(
        compute="_compute_is_obra_scrap",
        help="Indica que esta baixa parte do local compartilhado de "
        "materiais em obra, exigindo motivo e obra.",
    )
    move_id = fields.Many2one(
        comodel_name="stock.move",
        string="Movimento Pendente",
        help="Movimento pendente de retorno que esta baixa resolve, "
        "preenchido por StockPicking.action_register_obra_scrap. Cancelado "
        "quando a baixa é validada.",
    )

    @api.depends("location_id")
    def _compute_is_obra_scrap(self):
        obra_location = self._get_obra_stock_location()
        for scrap in self:
            scrap.is_obra_scrap = bool(obra_location) and (
                scrap.location_id == obra_location
            )

    def _cascade_obra(self):
        for scrap in self:
            plan = scrap._get_obra_plan()
            if not plan:
                continue
            root_plan = plan.root_id
            new_distribution = scrap._merge_obra_account(
                scrap.analytic_distribution, scrap.obra_id, root_plan
            )
            if new_distribution != (scrap.analytic_distribution or {}):
                scrap.analytic_distribution = new_distribution or False

    @api.model
    def _merge_obra_account(self, distribution, account, root_plan):
        """Merge `account` into `distribution`, replacing any account of
        `root_plan` while preserving accounts from other plans (mirrors
        cgl_purchase_analytic_equipment_custom's equivalent helper).
        """
        if not distribution:
            return {str(account.id): 100.0} if account else {}
        analytic_account = self.env["account.analytic.account"]
        new_distribution = {}
        for key, percentage in distribution.items():
            ids = [int(part) for part in key.split(",") if part.strip().isdigit()]
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
            new_distribution[new_key] = new_distribution.get(new_key, 0.0) + percentage
        return new_distribution

    @api.onchange("obra_id")
    def _onchange_obra_id(self):
        self._cascade_obra()

    @api.model_create_multi
    def create(self, vals_list):
        scraps = super().create(vals_list)
        scraps.filtered("obra_id")._cascade_obra()
        return scraps

    def write(self, vals):
        res = super().write(vals)
        if "obra_id" in vals:
            self._cascade_obra()
        return res

    @api.constrains("reason_code_id", "obra_id", "location_id", "state")
    def _check_obra_reason(self):
        """Only enforced at validation time (state == done): a draft scrap
        pre-filled by StockPicking.action_register_obra_scrap is allowed to
        sit without a reason/obra until the user completes and validates
        it.
        """
        for scrap in self:
            if scrap.state != "done" or not scrap.is_obra_scrap:
                continue
            if not scrap.reason_code_id:
                raise ValidationError(
                    _(
                        "Informe o motivo (perdido/roubado/danificado/"
                        "outro) ao dar baixa de material que não retornou "
                        "de obra."
                    )
                )
            if not scrap.obra_id:
                raise ValidationError(
                    _(
                        "Informe a Obra ao dar baixa de material que não "
                        "retornou de obra."
                    )
                )

    def action_validate(self):
        res = super().action_validate()
        # Flush before touching stock.move below: cancelling the pending
        # move invalidates ORM caches, and without an explicit flush first
        # the state='done' write above can be silently dropped (reverting
        # to 'draft' in the database) instead of persisted.
        self.flush_recordset()
        for scrap in self:
            if scrap.state == "done" and scrap.move_id.state not in (
                "done",
                "cancel",
            ):
                scrap.move_id._action_cancel()
        return res
