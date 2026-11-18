import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services import TransactionService, BudgetManager, AnalyticsService
from storage import DataRepository, FileStorage
from models import INCOME, EXPENSE


def main():
    ts = TransactionService()
    bm = BudgetManager()
    analytics = AnalyticsService(ts)
    repo = DataRepository(FileStorage("data.json"))
    repo.load(ts, bm)

    menu = """
1. Добавить операцию
2. Показать операции
3. Редактировать операцию
4. Удалить операцию
5. Категории и лимиты
6. Проверка лимита категории
7. Баланс и отчёты
8. Экспорт в CSV
9. Сохранить и выйти
"""
    while True:
        print(menu)
        choice = input("Выберите пункт: ").strip()

        if choice == "1":
            amount = float(input("Сумма: "))
            category = input("Категория: ").strip()
            ttype = "доход" if input("Тип (д/р): ").strip().lower() == "д" else "расход"
            comment = input("Комментарий: ").strip()
            t = ts.add(amount, category, ttype == "доход" and INCOME or EXPENSE, comment)
            over, spent, limit = bm.is_over_limit(category, t.tdate[:7], ts.all())
            print("Операция добавлена (id={})".format(t.tid))
            if over:
                print(f"ВНИМАНИЕ: превышен лимит категории '{category}' "
                      f"({spent} > {limit})")
        elif choice == "2":
            for t in ts.all():
                print(f"[{t.tid}] {t.tdate} {t.ttype:6} {t.category:12} "
                      f"{t.amount:10.2f} {t.comment}")
        elif choice == "3":
            tid = int(input("id операции: "))
            if ts.get(tid) is None:
                print("Операция не найдена")
                continue
            print("Оставьте поле пустым, чтобы не менять.")
            amount = input("Новая сумма: ").strip()
            category = input("Новая категория: ").strip()
            comment = input("Новый комментарий: ").strip()
            fields = {}
            if amount:
                fields["amount"] = float(amount)
            if category:
                fields["category"] = category
            if comment:
                fields["comment"] = comment
            ts.edit(tid, **fields)
            print("Операция обновлена")

        elif choice == "4":
            tid = int(input("id операции: "))
            if input("Удалить? (да/нет): ").strip().lower() == "да":
                ts.delete(tid)
                print("Удалено")

        elif choice == "5":
            for cat in bm.list_categories():
                lim = cat.limit if cat.limit is not None else "нет лимита"
                print(f"[{cat.cid}] {cat.name}: лимит {lim}")
            if input("Добавить категорию? (да/нет): ").strip().lower() == "да":
                bm.add_category(input("Название: ").strip())
            if input("Задать лимит? (да/нет): ").strip().lower() == "да":
                name = input("Категория: ").strip()
                bm.set_limit(name, float(input("Лимит: ")))
                print("Лимит сохранён")

        elif choice == "6":
            name = input("Категория: ").strip()
            month = input("Месяц (YYYY-MM): ").strip()
            over, spent, limit = bm.is_over_limit(name, month, ts.all())
            if limit is None:
                print("Лимит не установлен")
            elif over:
                print(f"Превышен лимит: потрачено {spent} из {limit}")
            else:
                print(f"В норме: потрачено {spent} из {limit}, осталось {limit - spent}")

        elif choice == "7":
            print(f"Общий баланс: {analytics.total_balance():.2f}")
            df = input("Период с (YYYY-MM-DD, пусто — всё время): ").strip() or None
            dt = input("по (YYYY-MM-DD): ").strip() or None
            r = analytics.report(df, dt)
            print(f"Доходы: {r['incomes']}, Расходы: {r['expenses']}")
            print("Топ-3 затратных категорий:")
            for cat, s in r["top_categories"]:
                print(f"  {cat}: {s:.2f}")

        elif choice == "8":
            path = repo.export_csv(ts.all())
            print("Экспортировано в", path)

        elif choice == "9":
            repo.save(ts, bm)
            print("Сохранено. До встречи!")
            break

        else:
            print("Неизвестный пункт меню")


if __name__ == "__main__":
    main()
