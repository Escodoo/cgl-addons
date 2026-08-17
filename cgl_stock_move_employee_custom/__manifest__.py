# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "CGL Stock Move Employee Custom",
    "summary": "Select the User behind stock withdrawals in "
    "Manufacturing, Repairs and Inventory/Delivery operations",
    "version": "18.0.1.0.0",
    "category": "Inventory",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/Escodoo/cgl-addons",
    "depends": [
        "stock",
        "mrp",
        "repair",
    ],
    "data": [
        "views/mrp_production_views.xml",
        "views/repair_order_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_line_views.xml",
    ],
}
