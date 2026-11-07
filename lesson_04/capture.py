"""Воспроизвести шесть планов на исходной коллекции logs.events."""
import os
from pathlib import Path
from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from pymongo import MongoClient

root = Path(__file__).resolve().parent
uri = os.getenv('MONGO_URI', 'mongodb://localhost:27037')
q1 = {'service': 'payments', 'level': 'error', 'duration_ms': {'$gt': 500}}
q2 = {'level': 'error'}
with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
    c = client.logs.events
    if c.count_documents({}) != 1200:
        raise SystemExit('Нужны исходные 1200 событий: запустите lesson_03/reset.py')
    c.drop_indexes()
    def capture(name, query, sort, limit=0):
        cursor = c.find(query).sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        plan = cursor.explain()
        (root / name).write_text(dumps(plan, json_options=RELAXED_JSON_OPTIONS, indent=2), encoding='utf-8')
        stats = plan['executionStats']
        stages, stage = [], stats['executionStages']
        while stage:
            stages.append(stage['stage'])
            stage = stage.get('inputStage')
        print(name, stats['nReturned'], stats['totalDocsExamined'], stats['totalKeysExamined'], ' → '.join(reversed(stages)))
    capture('plan-1.json', q1, [('ts', -1)])
    c.create_index([('service', 1), ('level', 1), ('ts', -1), ('duration_ms', 1)])
    capture('plan-2.json', q1, [('ts', -1)])
    c.drop_indexes()
    c.create_index([('duration_ms', 1), ('service', 1), ('level', 1), ('ts', -1)])
    capture('plan-3a.json', q1, [('ts', -1)])
    c.drop_indexes()
    c.create_index([('service', 1), ('level', 1), ('duration_ms', 1), ('ts', -1)])
    capture('plan-3b.json', q1, [('ts', -1)])
    c.drop_indexes()
    capture('plan-4-bez.json', q2, [('duration_ms', -1)], 10)
    c.create_index([('level', 1), ('duration_ms', -1)])
    capture('plan-4.json', q2, [('duration_ms', -1)], 10)
