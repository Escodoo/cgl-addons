# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "CGL Hour Appropriation Report Custom",
    "summary": "Show the hours of the Hour Appropriation SQL report as "
    "HH:MM, with totals that add up correctly",
    "version": "18.0.1.0.1",
    "category": "Reporting",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/Escodoo/cgl-addons",
    "depends": [
        "bi_sql_editor",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
