# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .models.bi_sql_view import EXTENSION_VIEW_NAME


def post_init_hook(env):
    """Extend the views of the SQL reports whose UI already exists.

    The report is created by hand in the SQL Views screen, so its views were
    generated before this module was installed.
    """
    env["bi.sql.view"].search([("state", "=", "ui_valid")])._sync_float_time_views()


def uninstall_hook(env):
    """Drop the extension views, which have no XML ID to be removed with the module."""
    # An archived extension still points to its parent and still restricts its
    # deletion, so it has to be found too.
    env["ir.ui.view"].with_context(active_test=False).search(
        [("name", "=", EXTENSION_VIEW_NAME)]
    ).unlink()
