import json
from src.schema import DocRecord
from src.reconcile import reconcile
from src.generate import generate

# Load the two committed records. We do not assume which is which —
# generate() derives each product's label from the record itself.
checklist = json.load(open("data/nepqa_checklist.json"))
record_a = DocRecord(**json.load(open("output/deye_record.json")))
record_b = DocRecord(**json.load(open("output/chisage_record.json")))

reconcile_result = reconcile(record_a, record_b)
draft = generate(record_a, record_b, reconcile_result, checklist)

with open("output/draft.md", "w") as f:
    f.write(draft)

print("Wrote output/draft.md")
print(draft)
