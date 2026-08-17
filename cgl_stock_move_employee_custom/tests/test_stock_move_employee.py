from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestStockMoveEmployee(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True}
        )
        cls.location_src = cls.env.ref("stock.stock_location_stock")
        cls.location_dest = cls.env.ref("stock.stock_location_customers")

        cls.employee_user = cls.env["res.users"].create(
            {
                "name": "Test Employee User",
                "login": "test_employee_user",
                "email": "test_employee_user@example.com",
            }
        )

    def _make_move(self, **extra_vals):
        vals = {
            "name": "Test Move",
            "product_id": self.product.id,
            "product_uom_qty": 1.0,
            "product_uom": self.product.uom_id.id,
            "location_id": self.location_src.id,
            "location_dest_id": self.location_dest.id,
        }
        vals.update(extra_vals)
        return self.env["stock.move"].create(vals)

    def test_user_can_be_set_manually(self):
        move = self._make_move(user_id=self.employee_user.id)
        self.assertEqual(move.user_id, self.employee_user)

    def test_user_is_optional(self):
        move = self._make_move()
        self.assertFalse(move.user_id)

    def test_user_can_be_changed(self):
        other_user = self.env["res.users"].create(
            {
                "name": "Another Employee User",
                "login": "another_employee_user",
                "email": "another_employee_user@example.com",
            }
        )
        move = self._make_move(user_id=self.employee_user.id)
        move.user_id = other_user
        self.assertEqual(move.user_id, other_user)

    def test_move_line_user_related_to_move(self):
        move = self._make_move(
            user_id=self.employee_user.id,
            move_line_ids=[
                Command.create(
                    {
                        "product_id": self.product.id,
                        "location_id": self.location_src.id,
                        "location_dest_id": self.location_dest.id,
                        "product_uom_id": self.product.uom_id.id,
                    }
                )
            ],
        )
        move_line = move.move_line_ids
        self.assertEqual(move_line.user_id, self.employee_user)

        other_user = self.env["res.users"].create(
            {
                "name": "Move Line User",
                "login": "move_line_user",
                "email": "move_line_user@example.com",
            }
        )
        move_line.user_id = other_user
        self.assertEqual(move.user_id, other_user)
