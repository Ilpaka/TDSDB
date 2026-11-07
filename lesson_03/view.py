"""Локальный просмотр данных и результатов практики в браузере."""
import html
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parent
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27037'), serverSelectionTimeoutMS=5000)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        page = parse_qs(urlparse(self.path).query).get('page', ['start'])[0]
        menu = [('start', 'Запуск'), ('created', 'Товары'), ('catalog', 'Каталог'), ('search', 'Поиск'), ('update', 'Изменения'), ('check', 'Проверка базы')]
        links = ''.join(f'<a href="/?page={key}">{title}</a>' for key, title in menu)
        shop, box = client.shop.products, client.sandbox.products
        if page == 'start':
            body = f"Подключение: MongoDB {client.server_info()['version']}\nshop.products: {shop.count_documents({})} документов\nsandbox.products: {box.count_documents({})} документов\n\nКоманда программы: python lesson_03/solution.py\nПодробный вывод последнего запуска: lesson_03/result.txt"
        elif page == 'created':
            docs = box.find({'_id': {'$in': ['p-101', 'p-102']}}, {'_id': 1, 'sku': 1, 'title': 1, 'price': 1})
            body = 'Товары после загрузки и приёмки\nИсходная коллекция shop.products: 21\nДобавленные в sandbox.products позиции:\n\n' + '\n'.join(str(d) for d in docs)
        elif page == 'catalog':
            docs = shop.find({}, {'_id': 0, 'sku': 1, 'title': 1, 'price': 1, 'rating': 1}).sort([('price', -1), ('sku', 1)]).limit(5)
            body = 'shop.products.find({}, projection).sort(price ↓, sku ↑).limit(5)\n\n' + '\n'.join(str(d) for d in docs)
        elif page == 'search':
            docs = shop.find({'category': 'ноутбуки'}, {'_id': 0, 'sku': 1, 'title': 1, 'price': 1}).sort([('price', -1), ('sku', 1)])
            body = 'Фильтр: {category: "ноутбуки"}; сортировка: цена ↓\nВсего: ' + str(shop.count_documents({'category': 'ноутбуки'})) + '\n\n' + '\n'.join(str(d) for d in docs)
        elif page == 'update':
            body = 'Журнал выполненной команды python lesson_03/solution.py\n\n' + (ROOT / 'result.txt').read_text().split('ПРИЁМКА ПОСТАВКИ', 1)[1]
        elif page == 'check':
            body = 'Текущая проверка MongoDB: sandbox.products\n' + f"Всего товаров: {box.count_documents({})}\nНовинки: {box.count_documents({'_id': {'$in': ['p-101', 'p-102']}})}\nУдалённый SKU-CP-018: {box.count_documents({'sku':'SKU-CP-018'})}\nБесплатная доставка аксессуарам: {box.count_documents({'category':'аксессуары','free_shipping':True})}\n\n" + (ROOT / 'check-result.txt').read_text()
        else:
            self.send_error(404); return
        title = dict(menu)[page]
        data = f'''<!doctype html><meta charset="utf-8"><title>Практика MongoDB — {title}</title><style>body{{font:16px system-ui;margin:38px auto;max-width:1120px;color:#152a3c}}header{{border-bottom:1px solid #cad5df}}nav{{display:flex;gap:20px;margin:20px 0}}a{{color:#126047}}pre{{background:#102b26;color:#effff7;padding:24px;border-radius:9px;white-space:pre-wrap;font:15px/1.8 monospace}}small{{color:#546c78}}</style><header><h1>Практика 01 · Каталог MongoDB</h1><small>Локальный просмотр данных и сохранённого вывода программы</small><nav>{links}</nav></header><h2>{title}</h2><pre>{html.escape(body)}</pre>'''.encode()
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

if __name__ == '__main__':
    print('Просмотр: http://127.0.0.1:8767', flush=True)
    HTTPServer(('127.0.0.1', 8767), Handler).serve_forever()
