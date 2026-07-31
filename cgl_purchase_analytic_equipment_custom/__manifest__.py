# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "CGL Purchase Analytic Equipment Custom",
    "summary": "Adds a Cost Center (Equipment) field to Purchase Orders",
    "version": "18.0.1.0.0",
    "category": "Purchases",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/Escodoo/cgl-addons",
    "depends": [
        "purchase_analytic_global",
    ],
    "data": [
        "views/purchase_order_views.xml",
    ],
    "demo": [
        "demo/purchase_analytic_equipment_demo.xml",
    ],
}
