# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "CGL Stock Mobilization Custom",
    "summary": "Rastreio de mobilização/desmobilização de materiais por obra",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/Escodoo/cgl-addons",
    "depends": [
        "stock_analytic",
        "scrap_reason_code",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/scrap_reason_code_data.xml",
        "views/res_config_settings_views.xml",
        "views/stock_scrap_views.xml",
        "views/stock_picking_views.xml",
        "views/obra_stock_report_views.xml",
    ],
    "installable": True,
}
