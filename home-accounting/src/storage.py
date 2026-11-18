import csv
import io
import json
import os


class FileStorage:

    def __init__(self, path="data.json"):
        self.path = path

    def save(self, transactions, categories, next_ids):
        data = {
            "transactions": [t.to_dict() for t in transactions],
            "categories": [c.to_dict() for c in categories],
            "next_ids": next_ids,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        if not os.path.exists(self.path):
            return {"transactions": [], "categories": [], "next_ids": {"t": 1, "c": 6}}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)


class DataRepository:

    def __init__(self, file_storage):
        self.storage = file_storage

    def save(self, transaction_service, budget_manager):
        self.storage.save(
            transaction_service.all(),
            budget_manager.list_categories(),
            {"t": transaction_service._next_id, "c": budget_manager._next_cid},
        )

    def load(self, transaction_service, budget_manager):
        data = self.storage.load()
        from models import Transaction, Category
        transaction_service._transactions = [Transaction.from_dict(d)
                                             for d in data["transactions"]]
        transaction_service._next_id = data["next_ids"].get("t", 1)
        budget_manager._categories = [Category.from_dict(d) for d in data["categories"]]
        budget_manager._next_cid = data["next_ids"].get("c", 6)

    @staticmethod
    def export_csv(transactions, path="export.csv"):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "date", "type", "category", "amount", "comment"])
        for t in transactions:
            writer.writerow([t.tid, t.tdate, t.ttype, t.category, t.amount, t.comment])
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(buf.getvalue())
        return path
