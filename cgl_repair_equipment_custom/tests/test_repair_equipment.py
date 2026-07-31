from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestRepairEquipment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {"name": "Test Product To Repair", "type": "consu"}
        )
        cls.equipment = cls.env["maintenance.equipment"].create(
            {"name": "Test Equipment"}
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.repair_type = cls.warehouse.repair_type_id

    def _make_repair(self, product_id=False, equipment_id=False):
        return self.env["repair.order"].create(
            {
                "picking_type_id": self.repair_type.id,
                "product_id": product_id,
                "equipment_id": equipment_id,
            }
        )

    def test_repair_with_product_only(self):
        repair = self._make_repair(product_id=self.product.id)
        self.assertEqual(repair.product_id, self.product)
        self.assertFalse(repair.equipment_id)

    def test_repair_with_equipment_only(self):
        repair = self._make_repair(equipment_id=self.equipment.id)
        self.assertEqual(repair.equipment_id, self.equipment)
        self.assertFalse(repair.product_id)

    def test_repair_with_both(self):
        repair = self._make_repair(
            product_id=self.product.id, equipment_id=self.equipment.id
        )
        self.assertEqual(repair.product_id, self.product)
        self.assertEqual(repair.equipment_id, self.equipment)

    def test_repair_without_product_or_equipment_raises(self):
        with self.assertRaises(ValidationError):
            self._make_repair()

    def test_removing_both_raises(self):
        repair = self._make_repair(product_id=self.product.id)
        with self.assertRaises(ValidationError):
            repair.product_id = False
