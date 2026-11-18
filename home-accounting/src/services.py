"""Сервисный слой: TransactionService, BudgetManager, AnalyticsService."""
import csv
import io
from datetime import date

from models import Transaction, Category, INCOME, EXPENSE


class TransactionService:
    """Модуль 1. Добавление, редактирование и удаление операций."""

    def __init__(self):
        self._transactions = []
        self._next_id = 1

    def add(self, amount, category, ttype, comment="", tdate=None):
        t = Transaction(amount, category, ttype, comment, tdate, self._next_id)
        self._transactions.append(t)
        self._next_id += 1
        return t

    def edit(self, tid, **fields):
        t = self.get(tid)
        if t is None:
            raise KeyError("Операция не найдена")
        allowed = {"amount", "category", "ttype", "comment", "tdate"}
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(t, key, round(float(value), 2) if key == "amount" else value)
        return t

    def delete(self, tid):
        t = self.get(tid)
        if t is None:
            raise KeyError("Операция не найдена")
        self._transactions.remove(t)
        return t

    def get(self, tid):
        for t in self._transactions:
            if t.tid == tid:
                return t
        return None

    def all(self, ttype=None):
        if ttype is None:
            return list(self._transactions)
        return [t for t in self._transactions if t.ttype == ttype]


class BudgetManager:
    """Модуль 2. Категории, месячные лимиты и проверка превышения."""

    DEFAULT_CATEGORIES = ["Еда", "Подписки", "Транспорт", "Жильё", "Развлечения"]

    def __init__(self):
        self._categories = [Category(name, cid=i + 1)
                            for i, name in enumerate(self.DEFAULT_CATEGORIES)]
        self._next_cid = len(self.DEFAULT_CATEGORIES) + 1

    def list_categories(self):
        return list(self._categories)

    def add_category(self, name):
        if self.find(name) is not None:
            raise ValueError("Категория уже существует")
        cat = Category(name, cid=self._next_cid)
        self._next_cid += 1
        self._categories.append(cat)
        return cat

    def rename_category(self, cid, new_name):
        if self.find(new_name) is not None:
            raise ValueError("Категория уже существует")
        cat = self.get_category(cid)
        if cat is None:
            raise KeyError("Категория не найдена")
        cat.name = new_name
        return cat

    def set_limit(self, cid_or_name, limit):
        cat = (self.get_category(cid_or_name) if isinstance(cid_or_name, int)
               else self.find(cid_or_name))
        if cat is None:
            raise KeyError("Категория не найдена")
        if limit is not None and limit < 0:
            raise ValueError("Лимит не может быть отрицательным")
        cat.limit = limit
        return cat

    def get_category(self, cid):
        for cat in self._categories:
            if cat.cid == cid:
                return cat
        return None

    def find(self, name):
        for cat in self._categories:
            if cat.name == name:
                return cat
        return None

    def is_over_limit(self, category_name, month, transactions):
        """Превышен ли лимит по категории за месяц?

        month — строка 'YYYY-MM'. Возвращает кортеж (превышено?, потрачено, лимит).
        Лимит не установлен — превышения нет.
        """
        cat = self.find(category_name)
        if cat is None or cat.limit is None:
            return False, 0.0, None
        spent = sum(t.amount for t in transactions
                    if t.category == category_name and t.ttype == EXPENSE
                    and t.tdate.startswith(month))
        return spent > cat.limit, round(spent, 2), cat.limit


class AnalyticsService:
    """Модуль 3. Баланс, расходы за период, топ-3 категорий."""

    def __init__(self, transaction_service):
        self._ts = transaction_service

    def total_balance(self):
        return round(sum(t.signed_amount() for t in self._ts.all()), 2)

    def expenses_in_period(self, date_from, date_to):
        return round(sum(t.amount for t in self._ts.all()
                         if t.ttype == EXPENSE and date_from <= t.tdate <= date_to), 2)

    def incomes_in_period(self, date_from, date_to):
        return round(sum(t.amount for t in self._ts.all()
                         if t.ttype == INCOME and date_from <= t.tdate <= date_to), 2)

    def top_categories(self, date_from=None, date_to=None, n=3):
        """Топ-n самых затратных категорий за период. По умолчанию — за всё время."""
        sums = {}
        for t in self._ts.all(ttype=EXPENSE):
            if date_from and t.tdate < date_from:
                continue
            if date_to and t.tdate > date_to:
                continue
            sums[t.category] = sums.get(t.category, 0.0) + t.amount
        ranked = sorted(sums.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:n]

    def report(self, date_from=None, date_to=None):
        """FinancialReport: сводка за период."""
        expenses = self.expenses_in_period(date_from, date_to) if date_from else \
            round(sum(t.amount for t in self._ts.all(ttype=EXPENSE)), 2)
        incomes = self.incomes_in_period(date_from, date_to) if date_from else \
            round(sum(t.amount for t in self._ts.all(ttype=INCOME)), 2)
        return {
            "period": f"{date_from or 'начало'} — {date_to or 'сейчас'}",
            "incomes": incomes,
            "expenses": expenses,
            "balance": round(incomes - expenses, 2),
            "top_categories": self.top_categories(date_from, date_to),
        }
