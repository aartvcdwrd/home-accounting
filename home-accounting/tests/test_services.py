"""Юнит-тесты сервисов и хранилища."""
import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from models import Transaction, Category, INCOME, EXPENSE
from services import TransactionService, BudgetManager, AnalyticsService
from storage import FileStorage, DataRepository


class TestTransactions(unittest.TestCase):
    def setUp(self):
        self.ts = TransactionService()

    def test_add_operation(self):
        t = self.ts.add(1000, "Еда", EXPENSE, "продукты")
        self.assertEqual(t.amount, 1000)
        self.assertEqual(t.ttype, EXPENSE)
        self.assertEqual(t.tdate, date.today().isoformat())

    def test_negative_amount_rejected(self):
        with self.assertRaises(ValueError):
            self.ts.add(-5, "Еда", EXPENSE)

    def test_wrong_type_rejected(self):
        with self.assertRaises(ValueError):
            self.ts.add(5, "Еда", "перевод")

    def test_edit_and_delete(self):
        t = self.ts.add(100, "Еда", EXPENSE)
        self.ts.edit(t.tid, amount=200)
        self.assertEqual(self.ts.get(t.tid).amount, 200)
        self.ts.delete(t.tid)
        self.assertIsNone(self.ts.get(t.tid))

    def test_delete_missing_raises(self):
        with self.assertRaises(KeyError):
            self.ts.delete(999)


class TestBudget(unittest.TestCase):
    def setUp(self):
        self.bm = BudgetManager()

    def test_default_categories(self):
        names = [c.name for c in self.bm.list_categories()]
        self.assertIn("Еда", names)

    def test_add_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            self.bm.add_category("Еда")

    def test_over_limit(self):
        self.bm.set_limit("Еда", 500)
        ts = TransactionService()
        ts.add(300, "Еда", EXPENSE)
        over, spent, limit = self.bm.is_over_limit("Еда", date.today().isoformat()[:7], ts.all())
        self.assertFalse(over)
        ts.add(300, "Еда", EXPENSE)
        over, spent, limit = self.bm.is_over_limit("Еда", date.today().isoformat()[:7], ts.all())
        self.assertTrue(over)
        self.assertEqual(spent, 600.0)

    def test_other_month_not_counted(self):
        self.bm.set_limit("Еда", 100)
        ts = TransactionService()
        ts.add(999, "Еда", EXPENSE, tdate="1999-01-01")
        over, _, _ = self.bm.is_over_limit("Еда", date.today().isoformat()[:7], ts.all())
        self.assertFalse(over)


class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.ts = TransactionService()
        self.an = AnalyticsService(self.ts)

    def test_balance(self):
        self.ts.add(1000, "Зарплата", INCOME)
        self.ts.add(400, "Еда", EXPENSE)
        self.assertEqual(self.an.total_balance(), 600.0)

    def test_expenses_in_period(self):
        self.ts.add(100, "Еда", EXPENSE, tdate="2026-01-05")
        self.ts.add(200, "Еда", EXPENSE, tdate="2026-02-10")
        self.assertEqual(self.an.expenses_in_period("2026-01-01", "2026-01-31"), 100.0)

    def test_top_categories(self):
        self.ts.add(100, "Еда", EXPENSE)
        self.ts.add(300, "Транспорт", EXPENSE)
        self.ts.add(200, "Развлечения", EXPENSE)
        self.ts.add(50, "Еда", EXPENSE)
        top = self.an.top_categories()
        self.assertEqual([c for c, _ in top], ["Транспорт", "Развлечения", "Еда"])


class TestStorage(unittest.TestCase):
    def test_save_and_load_roundtrip(self):
        ts = TransactionService()
        bm = BudgetManager()
        ts.add(1000, "Зарплата", INCOME, "оклад")
        ts.add(250, "Еда", EXPENSE, "кофе")
        bm.set_limit("Еда", 1000)

        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            repo = DataRepository(FileStorage(path))
            repo.save(ts, bm)
            ts2, bm2 = TransactionService(), BudgetManager()
            repo.load(ts2, bm2)
            self.assertEqual(len(ts2.all()), 2)
            self.assertEqual(ts2.all()[0].comment, "оклад")
            self.assertEqual(bm2.find("Еда").limit, 1000)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
