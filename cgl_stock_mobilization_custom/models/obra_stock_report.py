# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


class ObraStockReport(models.Model):
    """Reporting fact table: one row per mobilization/demobilization move
    or per write-off (scrap) of material that did not return from an obra.

    Not stored: it is a live SQL view (`_auto = False`), so it always
    reflects the current state of `stock.move` / `stock.scrap` with no
    separate data to keep in sync.
    """

    _name = "cgl.obra.stock.report"
    _description = "Relatório de Materiais em Obra"
    _auto = False
    _order = "date desc"

    tipo = fields.Selection(
        [
            ("mobilizado", "Mobilizado"),
            ("desmobilizado", "Desmobilizado"),
            ("baixa", "Baixa (não retornou)"),
        ],
        readonly=True,
    )
    reason_code_id = fields.Many2one(
        comodel_name="scrap.reason.code", string="Motivo", readonly=True
    )
    obra_id = fields.Many2one(
        comodel_name="account.analytic.account", string="Obra", readonly=True
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Produto", readonly=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Empresa", readonly=True
    )
    quantity = fields.Float(string="Quantidade", readonly=True)
    value = fields.Monetary(
        string="Valor", currency_field="company_currency_id", readonly=True
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Moeda", readonly=True
    )
    date = fields.Datetime(string="Data", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    -sm.id AS id,
                    CASE
                        WHEN spt.sequence_code = 'MOB' THEN 'mobilizado'
                        ELSE 'desmobilizado'
                    END AS tipo,
                    NULL::int4 AS reason_code_id,
                    obra.id AS obra_id,
                    sm.product_id AS product_id,
                    sm.company_id AS company_id,
                    rc.currency_id AS company_currency_id,
                    sm.quantity AS quantity,
                    COALESCE(ABS(svl.value), 0.0) AS value,
                    sm.date AS date
                FROM stock_move sm
                JOIN stock_picking sp ON sp.id = sm.picking_id
                JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
                -- res_company.obra_analytic_plan_id is configured per
                -- company (Inventário > Configuração > Definições), so it
                -- is looked up here per row via sm.company_id rather than
                -- baked into the view at init() time.
                JOIN res_company rc ON rc.id = sm.company_id
                LEFT JOIN stock_valuation_layer svl
                    ON svl.stock_move_id = sm.id
                LEFT JOIN LATERAL (
                    -- Same account-id extraction expression as
                    -- analytic.mixin._query_analytic_accounts(), so this
                    -- benefits from the GIN index that mixin already
                    -- creates on analytic_distribution.
                    SELECT aaa.id
                    FROM account_analytic_account aaa
                    WHERE aaa.plan_id = rc.obra_analytic_plan_id
                      AND aaa.id::text = ANY(regexp_split_to_array(
                          jsonb_path_query_array(
                              COALESCE(sm.analytic_distribution, '{{}}'::jsonb),
                              '$.keyvalue()."key"'
                          )::text,
                          '\\D+'
                      ))
                    LIMIT 1
                ) obra ON true
                WHERE sm.state = 'done'
                  AND spt.sequence_code IN ('MOB', 'DESMOB')
                  AND sm.scrap_id IS NULL

                UNION ALL

                SELECT
                    ss.id AS id,
                    'baixa' AS tipo,
                    ss.reason_code_id AS reason_code_id,
                    ss.obra_id AS obra_id,
                    ss.product_id AS product_id,
                    ss.company_id AS company_id,
                    rc2.currency_id AS company_currency_id,
                    ssm.quantity AS quantity,
                    COALESCE(ABS(svl2.value), 0.0) AS value,
                    ss.date_done AS date
                FROM stock_scrap ss
                JOIN stock_move ssm ON ssm.scrap_id = ss.id
                JOIN res_company rc2 ON rc2.id = ss.company_id
                LEFT JOIN stock_valuation_layer svl2
                    ON svl2.stock_move_id = ssm.id
                WHERE ss.state = 'done'
            )
        """)
