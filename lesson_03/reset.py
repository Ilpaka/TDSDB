"""Восстановить только три учебные коллекции из файлов курса."""
import os
from pathlib import Path
from bson.json_util import loads
from pymongo import MongoClient

root = Path(__file__).resolve().parent / 'data'
with MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27037')) as client:
    for path in sorted(root.glob('*.json')):
        database, collection = path.stem.split('.', 1)
        docs = loads(path.read_text(encoding='utf-8'))
        target = client[database][collection]
        target.drop()
        target.insert_many(docs)
        print(f'{database}.{collection}: загружено {target.count_documents({})}')
