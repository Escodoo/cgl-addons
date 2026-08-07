# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "CGL MRP Workorder Employee Custom",
    "summary": "Track the employee who performed the activity in "
    "Manufacturing Order work order time tracking",
    "version": "18.0.1.0.0",
    "category": "Manufacturing",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/Escodoo/cgl-addons",
    "depends": [
        "mrp",
        "hr",
    ],
    "data": [
        "views/mrp_workorder_views.xml",
    ],
}
