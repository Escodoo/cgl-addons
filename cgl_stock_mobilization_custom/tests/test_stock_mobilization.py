# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestStockMobilization(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.projeto_plan = cls.env["account.analytic.plan"].create(
            {"name": "Test Projeto"}
        )
        warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.wh_location = warehouse.lot_stock_id
        cls.obra_location = cls.env["stock.location"].create(
            {
                "name": "Test Materiais em Obra",
                "usage": "internal",
                "location_id": cls.wh_location.location_id.id,
            }
        )
        cls.env.company.write(
            {
                "obra_stock_location_id": cls.obra_location.id,
                "obra_analytic_plan_id": cls.projeto_plan.id,
            }
        )
        cls.env.company._setup_obra_picking_types()

        cls.mob_type = cls.env["stock.picking.type"].search(
            [
                ("sequence_code", "=", "MOB"),
                ("warehouse_id", "=", warehouse.id),
            ],
            limit=1,
        )
        cls.desmob_type = cls.env["stock.picking.type"].search(
            [
                ("sequence_code", "=", "DESMOB"),
                ("warehouse_id", "=", warehouse.id),
            ],
            limit=1,
        )
        cls.reason_perdido = cls.env.ref(
            "cgl_stock_mobilization_custom.scrap_reason_perdido"
        )

        # Created here rather than pulled from demo data, so the suite is
        # meaningful on a database installed with --without-demo.
        analytic_account = cls.env["account.analytic.account"]
        cls.obra_1 = analytic_account.create(
            {"name": "Test Obra 1", "plan_id": cls.projeto_plan.id}
        )
        cls.obra_2 = analytic_account.create(
            {"name": "Test Obra 2", "plan_id": cls.projeto_plan.id}
        )
        cls.other_plan = cls.env["account.analytic.plan"].create(
            {"name": "Test Other Plan"}
        )
        cls.other_account = analytic_account.create(
            {"name": "Test Other Account", "plan_id": cls.other_plan.id}
        )

        cls.product = cls.env["product.product"].create(
            {"name": "Test Material", "is_storable": True}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.wh_location, 50.0
        )

    # -- test helpers -------------------------------------------------

    def _mobilize(self, qty, obra):
        picking_type = self.mob_type
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.display_name,
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "product_uom": self.product.uom_id.id,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": (
                                picking_type.default_location_dest_id.id
                            ),
                            "analytic_distribution": {str(obra.id): 100.0},
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity = qty
        picking.move_ids.picked = True
        picking.button_validate()
        return picking

    def _mobilize_and_partially_return(self, mobilized, returned, obra):
        self._mobilize(mobilized, obra)
        picking_type = self.desmob_type
        desmob = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.display_name,
                            "product_id": self.product.id,
                            "product_uom_qty": mobilized,
                            "product_uom": self.product.uom_id.id,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": (
                                picking_type.default_location_dest_id.id
                            ),
                            "analytic_distribution": {str(obra.id): 100.0},
                        },
                    )
                ],
            }
        )
        desmob.action_confirm()
        desmob.action_assign()
        desmob.move_ids.quantity = returned
        desmob.move_ids.picked = True
        result = desmob.button_validate()
        if (
            isinstance(result, dict)
            and result.get("res_model") == "stock.backorder.confirmation"
        ):
            self.env["stock.backorder.confirmation"].with_context(
                **result["context"]
            ).create({}).process()
        backorder = self.env["stock.picking"].search([("backorder_id", "=", desmob.id)])
        return desmob, backorder

    def _validate_obra_scrap(self, scrap):
        scrap.write(
            {
                "reason_code_id": self.reason_perdido.id,
                "justificativa": "Test justification",
            }
        )
        scrap.action_validate()

    # -- setup / hook ---------------------------------------------------

    def test_picking_types_point_to_shared_obra_location(self):
        self.assertEqual(self.mob_type.default_location_dest_id, self.obra_location)
        self.assertEqual(self.desmob_type.default_location_src_id, self.obra_location)

    def test_picking_types_are_mutual_returns(self):
        self.assertEqual(self.mob_type.return_picking_type_id, self.desmob_type)
        self.assertEqual(self.desmob_type.return_picking_type_id, self.mob_type)

    # -- stock.move._get_obra_account ------------------------------------

    def test_get_obra_account_extracts_projeto_plan_account(self):
        move = self._mobilize(5, self.obra_1).move_ids
        self.assertEqual(move._get_obra_account(), self.obra_1)

    def test_get_obra_account_ignores_other_plans(self):
        move = self._mobilize(5, self.obra_1).move_ids
        move.analytic_distribution = {
            f"{self.obra_1.id},{self.other_account.id}": 100.0
        }
        self.assertEqual(move._get_obra_account(), self.obra_1)

    def test_get_obra_account_empty_without_distribution(self):
        move = self._mobilize(5, self.obra_1).move_ids
        move.analytic_distribution = False
        self.assertFalse(move._get_obra_account())

    # -- "Devolução" (return) button carries the obra over ----------------

    def test_return_wizard_preserves_analytic_distribution(self):
        """Regression: clicking "Devolução" must not require re-selecting
        the obra -- Odoo's stock.return.picking copies the original move
        (including analytic_distribution) rather than starting blank."""
        mob = self._mobilize(10, self.obra_1)
        return_wizard = (
            self.env["stock.return.picking"]
            .with_context(active_id=mob.id, active_model="stock.picking")
            .create({})
        )
        return_wizard.product_return_moves.quantity = 10
        res = return_wizard.action_create_returns()
        desmob = self.env["stock.picking"].browse(res["res_id"])

        self.assertEqual(desmob.picking_type_id, self.desmob_type)
        self.assertEqual(
            desmob.move_ids.analytic_distribution, {str(self.obra_1.id): 100.0}
        )

    # -- partial return -> backorder represents "pending" ------------------

    def test_partial_return_creates_backorder_at_obra_location(self):
        desmob, backorder = self._mobilize_and_partially_return(10, 6, self.obra_1)
        self.assertEqual(desmob.state, "done")
        self.assertTrue(backorder)
        self.assertEqual(backorder.move_ids.product_uom_qty, 4)
        self.assertEqual(backorder.location_id, self.obra_location)

    def test_show_register_obra_scrap_true_only_with_pending_qty(self):
        _, backorder = self._mobilize_and_partially_return(10, 6, self.obra_1)
        self.assertTrue(backorder.show_register_obra_scrap)

        fully_returned, no_backorder = self._mobilize_and_partially_return(
            3, 3, self.obra_1
        )
        self.assertFalse(no_backorder)
        self.assertFalse(fully_returned.show_register_obra_scrap)

    # -- action_register_obra_scrap ----------------------------------------

    def test_register_obra_scrap_prefills_pending_line(self):
        _, backorder = self._mobilize_and_partially_return(10, 6, self.obra_1)

        action = backorder.action_register_obra_scrap()
        scrap = self.env["stock.scrap"].browse(action["res_id"])

        self.assertEqual(scrap.product_id, self.product)
        self.assertEqual(scrap.scrap_qty, 4)
        self.assertEqual(scrap.location_id, self.obra_location)
        self.assertEqual(scrap.obra_id, self.obra_1)
        self.assertEqual(scrap.move_id, backorder.move_ids)
        self.assertEqual(scrap.picking_id, backorder)
        self.assertFalse(scrap.reason_code_id)

    def test_register_obra_scrap_no_pending_raises(self):
        mob = self._mobilize(5, self.obra_1)
        with self.assertRaises(UserError):
            mob.action_register_obra_scrap()

    def test_validating_scrap_cancels_pending_move(self):
        _, backorder = self._mobilize_and_partially_return(10, 6, self.obra_1)
        action = backorder.action_register_obra_scrap()
        scrap = self.env["stock.scrap"].browse(action["res_id"])

        self._validate_obra_scrap(scrap)

        self.assertEqual(scrap.state, "done")
        # backorder.move_ids also includes the scrap's own generated move
        # (kept for traceability via picking_id) -- only the original
        # pending desmob move should end up cancelled.
        original_moves = backorder.move_ids.filtered(lambda m: not m.scrap_id)
        self.assertEqual(original_moves.mapped("state"), ["cancel"])
        self.assertFalse(backorder.show_register_obra_scrap)

    def test_register_obra_scrap_is_idempotent(self):
        """A second click after the pending qty is resolved finds nothing
        left to do instead of creating a duplicate scrap."""
        _, backorder = self._mobilize_and_partially_return(10, 6, self.obra_1)
        action = backorder.action_register_obra_scrap()
        scrap = self.env["stock.scrap"].browse(action["res_id"])
        self._validate_obra_scrap(scrap)

        with self.assertRaises(UserError):
            backorder.action_register_obra_scrap()

    def test_validating_one_scrap_does_not_cancel_a_sibling_pending_move(self):
        """Regression: with two pending lines for the same product on one
        picking, validating one scrap must only cancel the move it was
        created for (scrap.move_id), not every pending move that happens to
        share the same product."""
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.obra_location, 10.0
        )
        picking_type = self.desmob_type
        backorder = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.display_name,
                            "product_id": self.product.id,
                            "product_uom_qty": 3,
                            "product_uom": self.product.uom_id.id,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": (
                                picking_type.default_location_dest_id.id
                            ),
                            "analytic_distribution": {str(self.obra_1.id): 100.0},
                        },
                    )
                    for _ in range(2)
                ],
            }
        )
        # Left in "draft" deliberately: action_confirm() would merge two
        # identical moves for the same product/locations into one, which
        # would defeat the point of this test (two independent pending
        # moves). A draft move already satisfies the "pending" predicate.

        action = backorder.action_register_obra_scrap()
        scraps = self.env["stock.scrap"].search(action["domain"])
        self.assertEqual(len(scraps), 2)
        self._validate_obra_scrap(scraps[0])

        self.assertEqual(scraps[0].move_id.state, "cancel")
        self.assertNotEqual(scraps[1].move_id.state, "cancel")

    # -- obra_id cascades into analytic_distribution -----------------------

    def test_obra_id_writes_into_analytic_distribution(self):
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "obra_id": self.obra_1.id,
            }
        )
        self.assertEqual(scrap.analytic_distribution, {str(self.obra_1.id): 100.0})

    def test_obra_id_preserves_other_plan_accounts(self):
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "analytic_distribution": {str(self.other_account.id): 100.0},
            }
        )

        scrap.obra_id = self.obra_1.id

        distribution = scrap.analytic_distribution
        self.assertEqual(len(distribution), 1)
        ((key, percentage),) = distribution.items()
        ids = {int(part) for part in key.split(",")}
        self.assertEqual(ids, {self.other_account.id, self.obra_1.id})
        self.assertEqual(percentage, 100.0)

    def test_changing_obra_id_replaces_previous_obra(self):
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "obra_id": self.obra_1.id,
            }
        )

        scrap.obra_id = self.obra_2.id

        self.assertEqual(scrap.analytic_distribution, {str(self.obra_2.id): 100.0})

    # -- is_obra_scrap / required reason & obra at validation ---------------

    def test_is_obra_scrap_true_only_at_obra_location(self):
        scrap_at_obra = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.obra_location.id,
            }
        )
        scrap_elsewhere = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.wh_location.id,
            }
        )
        self.assertTrue(scrap_at_obra.is_obra_scrap)
        self.assertFalse(scrap_elsewhere.is_obra_scrap)

    def test_draft_obra_scrap_can_be_incomplete(self):
        """A pre-filled draft (as created by action_register_obra_scrap) is
        allowed to sit without a reason/obra -- only validating enforces
        them."""
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.obra_location.id,
            }
        )
        self.assertEqual(scrap.state, "draft")

    def test_validate_obra_scrap_without_reason_blocked(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.obra_location, 5.0
        )
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.obra_location.id,
            }
        )

        with self.assertRaises(ValidationError):
            scrap.action_validate()

    def test_validate_obra_scrap_without_obra_blocked(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.obra_location, 5.0
        )
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.obra_location.id,
                "reason_code_id": self.reason_perdido.id,
            }
        )

        with self.assertRaises(ValidationError):
            scrap.action_validate()

    def test_normal_scrap_outside_obra_unaffected(self):
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product.id,
                "scrap_qty": 1,
                "product_uom_id": self.product.uom_id.id,
                "location_id": self.wh_location.id,
            }
        )
        scrap.action_validate()
        self.assertEqual(scrap.state, "done")

    # -- cgl.obra.stock.report --------------------------------------------

    def test_report_reconciles_mobilized_returned_and_scrapped(self):
        _, backorder = self._mobilize_and_partially_return(10, 6, self.obra_1)
        action = backorder.action_register_obra_scrap()
        scrap = self.env["stock.scrap"].browse(action["res_id"])
        self._validate_obra_scrap(scrap)

        report = self.env["cgl.obra.stock.report"].search(
            [("obra_id", "=", self.obra_1.id)]
        )
        by_type = {
            tipo: sum(
                report.filtered(lambda r, tipo=tipo: r.tipo == tipo).mapped("quantity")
            )
            for tipo in ("mobilizado", "desmobilizado", "baixa")
        }
        self.assertEqual(by_type["mobilizado"], 10)
        self.assertEqual(by_type["desmobilizado"], 6)
        self.assertEqual(by_type["baixa"], 4)

    def test_report_does_not_double_count_scrap_move(self):
        """Regression: the scrap's own generated move shares picking_id with
        the Desmobilização backorder (kept for traceability), and used to
        also get counted a second time as a "desmobilizado" row."""
        _, backorder = self._mobilize_and_partially_return(10, 6, self.obra_1)
        action = backorder.action_register_obra_scrap()
        scrap = self.env["stock.scrap"].browse(action["res_id"])
        self._validate_obra_scrap(scrap)

        report = self.env["cgl.obra.stock.report"].search(
            [("obra_id", "=", self.obra_1.id), ("tipo", "=", "desmobilizado")]
        )
        self.assertEqual(len(report), 1)
        self.assertEqual(report.quantity, 6)
