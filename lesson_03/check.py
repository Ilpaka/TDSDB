"""Самопроверка практической работы 01.

Проверяет не ваш код, а его результат: во что превратилась база после
приёмки поставки. Так же принимают работу и в жизни — по состоянию данных.

    bash ../stend/load.sh     # чистые данные
    python3 solution.py       # ваше решение (или эталонное)
    python3 check.py          # проверка

Каждая строка отчёта — отдельное требование задания.
"""

import os
import sys
from pymongo import MongoClient

URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(URI)
products = client["shop"]["products"]
box = client["sandbox"]["products"]

checks = []


def check(name, got, expected):
    ok = got == expected
    checks.append(ok)
    mark = "✓" if ok else "✗"
    tail = "" if ok else f"   ← ожидалось {expected!r}"
    print(f" {mark} {name:<46} {got!r}{tail}")


print("Задача 1 · витрина каталога")
check("товаров в каталоге shop.products", products.count_documents({}), 21)
check("ноутбуков", products.count_documents({"category": "ноутбуки"}), 5)
top = products.find({}, {"_id": 0, "title": 1}).sort("price", -1).limit(1)
check("самый дорогой товар", next(top)["title"], "Ноутбук Apple MacBook Air 13")

print("\nЗадача 2 · приёмка поставки")
check("всего позиций в песочнице", box.count_documents({}), 22)
check("новинка p-101 заведена", box.count_documents({"_id": "p-101"}), 1)
check("новинка p-102 заведена", box.count_documents({"_id": "p-102"}), 1)
check("снятый с продажи SKU-CP-018 удалён",
      box.count_documents({"sku": "SKU-CP-018"}), 0)
check("бесплатная доставка у аксессуаров",
      box.count_documents({"category": "аксессуары", "free_shipping": True}), 5)
check("остаток по SKU-NB-001",
      (box.find_one({"sku": "SKU-NB-001"}) or {}).get("qty_total"), 5)
check("остаток по SKU-PH-006",
      (box.find_one({"sku": "SKU-PH-006"}) or {}).get("qty_total"), 12)
check("остаток по SKU-PR-010",
      (box.find_one({"sku": "SKU-PR-010"}) or {}).get("qty_total"), 3)
check("эталонная база shop не тронута",
      products.count_documents({"free_shipping": True}), 0)

passed, total = sum(checks), len(checks)
print(f"\nПройдено {passed} из {total}")
if passed != total:
    print("Данные разъехались? Начните заново: bash ../stend/load.sh")
client.close()
sys.exit(0 if passed == total else 1)
