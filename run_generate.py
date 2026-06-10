import json
from src.schema import DocRecord
from src.reconcile import reconcile
from src.generate import generate

checklist = json.load(open("data/nepqa_checklist.json"))
deye = DocRecord(**json.load(open("output/deye_record.json")))
chisage = DocRecord(**json.load(open("output/chisage_record.json")))

reconcile_result = reconcile(deye, chisage)
draft = generate(deye, chisage, reconcile_result, checklist)

with open("output/draft.md", "w") as f:
    f.write(draft)

print("Wrote output/draft.md")
print(draft)
