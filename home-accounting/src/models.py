"""Модели данных: Transaction и Category."""
from datetime import date

INCOME = "income"
EXPENSE = "expense"


class Transaction:
    """Операция: сумма, категория, дата, тип (доход/расход), комментарий."""

    def __init__(self, amount, category, ttype, comment="", tdate=None, tid=None):
        if amount is None or amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")
        if ttype not in (INCOME, EXPENSE):
            raise ValueError("Тип должен быть 'income' или 'expense'")
        self.tid = tid
        self.amount = round(float(amount), 2)
        self.category = category
        self.ttype = ttype
        self.comment = comment
        self.tdate = tdate or date.today().isoformat()

    def to_dict(self):
        return {
            "tid": self.tid,
            "amount": self.amount,
            "category": self.category,
            "ttype": self.ttype,
            "comment": self.comment,
            "tdate": self.tdate,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["amount"], d["category"], d["ttype"], d.get("comment", ""),
                   d.get("tdate"), d.get("tid"))

    def signed_amount(self):
        """Доход со знаком плюс, расход — минус."""
        return self.amount if self.ttype == INCOME else -self.amount


class Category:
    """Категория трат с опциональным месячным лимитом."""

    def __init__(self, name, limit=None, cid=None):
        self.cid = cid
        self.name = name
        self.limit = limit

    def to_dict(self):
        return {"cid": self.cid, "name": self.name, "limit": self.limit}

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d.get("limit"), d.get("cid"))
