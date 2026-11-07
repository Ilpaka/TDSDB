"""ПР-01: каталог товаров и приёмка поставки в песочнице."""
import os
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27037')
ARRIVED = {'SKU-NB-001': 5, 'SKU-PH-006': 12, 'SKU-PR-010': 3}
NEW_ITEMS = [
    {'_id': 'p-101', 'sku': 'SKU-AC-101', 'title': 'Подставка для ноутбука', 'brand': 'OEM', 'category': 'аксессуары', 'price': 2490, 'reviews': 0},
    {'_id': 'p-102', 'sku': 'SKU-AC-102', 'title': 'Чехол для планшета', 'brand': 'OEM', 'category': 'аксессуары', 'price': 1890, 'reviews': 0},
]


def catalog_page(products, category=None, page=1, per_page=5, sort_field='price', desc=True):
    if page < 1 or per_page < 1:
        raise ValueError('page и per_page должны быть положительными')
    if sort_field not in {'price', 'rating', 'title', 'sku'}:
        raise ValueError('Недопустимое поле сортировки')
    query = {'category': category} if category else {}
    projection = {'_id': 0, 'sku': 1, 'title': 1, 'price': 1, 'rating': 1}
    sort = [(sort_field, -1 if desc else 1)]
    if sort_field != 'sku':
        sort.append(('sku', 1))
    total = products.count_documents(query)
    items = list(products.find(query, projection).sort(sort).skip((page - 1) * per_page).limit(per_page))
    return items, total


def receive_supply(box):
    print('\nПРИЁМКА ПОСТАВКИ')
    changed = 0
    for sku, quantity in ARRIVED.items():
        result = box.update_one({'sku': sku}, {'$inc': {'qty_total': quantity}})
        print(f'{sku}: найдено {result.matched_count}, изменено {result.modified_count}, прибавлено {quantity}')
        changed += result.modified_count
    try:
        inserted = len(box.insert_many(NEW_ITEMS, ordered=False).inserted_ids)
    except BulkWriteError as exc:
        errors = exc.details['writeErrors']
        if any(error['code'] != 11000 for error in errors) or exc.details.get('writeConcernErrors'):
            raise
        inserted = exc.details['nInserted']
        print(f'Уже существующие позиции пропущены: {len(errors)}')
    print(f'Новых позиций: {inserted}')
    query = {'sku': {'$in': ['SKU-CP-018']}}
    print(f"Перед удалением найдено: {box.count_documents(query)}")
    for doc in box.find(query, {'_id': 1, 'sku': 1, 'title': 1, 'price': 1}):
        print(doc)
    deleted = box.delete_many(query).deleted_count
    category = {'category': 'аксессуары'}
    eligible = box.count_documents(category)
    shipping = box.update_many(category, {'$set': {'free_shipping': True}})
    print(f'Удалено: {deleted}; аксессуаров: {eligible}; доставка изменена: {shipping.modified_count}')
    print(f'Остатки изменены: {changed}; всего в sandbox.products: {box.count_documents({})}')


def main():
    with MongoClient(URI, serverSelectionTimeoutMS=5000) as client:
        client.admin.command('ping')
        print('Подключение к MongoDB успешно; база shop, коллекция products')
        products = client.shop.products
        for category, page, size in [(None, 1, 5), ('ноутбуки', 1, 3), ('ноутбуки', 2, 3), ('ноутбуки', 9, 3)]:
            items, total = catalog_page(products, category, page, size)
            print(f'\nКатегория: {category or "все"}; страница: {page}; всего: {total}; найдено: {len(items)}')
            for item in items:
                print(f"  {item['sku']} | {item['title']} | {item['price']} ₽ | рейтинг {item.get('rating', 'нет')}")
        receive_supply(client.sandbox.products)


if __name__ == '__main__':
    main()
