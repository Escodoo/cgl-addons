from odoo import SUPERUSER_ID, api

from odoo.addons.cgl_hour_appropriation_report_custom.hooks import post_init_hook


def migrate(cr, version):
    """Refresh the extension views of the reports that already have their UI.

    The extensions are created by code, so they are not updated with the module.
    Every later version that changes them needs a migration calling this.
    """
    post_init_hook(api.Environment(cr, SUPERUSER_ID, {}))
