import json
from src.schema import DocRecord
from src.reconcile import reconcile

a = DocRecord(**json.load(open("output/deye_record.json")))
b = DocRecord(**json.load(open("output/chisage_record.json")))

result = reconcile(a, b)
print(json.dumps(result, indent=2))