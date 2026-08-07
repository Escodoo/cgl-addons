# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tests.common import TransactionCase


class TestMrpWorkorderDuration(TransactionCase):
    def test_duration_hours_converts_minutes_to_hours(self):
        workcenter = self.env["mrp.workcenter"].create({"name": "Test Workcenter"})
        productivity = self.env["mrp.workcenter.productivity"].create(
            {
                "workcenter_id": workcenter.id,
                "loss_id": self.env.ref("mrp.block_reason7").id,
                "date_start": datetime(2026, 8, 11, 8, 6, 19),
                "date_end": datetime(2026, 8, 11, 10, 10, 19),
            }
        )
        self.assertAlmostEqual(productivity.duration, 124.0, places=2)
        self.assertAlmostEqual(productivity.duration_hours, 124.0 / 60.0, places=4)
