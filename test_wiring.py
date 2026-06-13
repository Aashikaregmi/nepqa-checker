"""Validate the graph mechanics with a FAKE llm (no API key, no network).

Two parts:
  PART A — the verifier LOOP: the fake submits a FABRICATED quote first, so
           we watch verify fail and force a retry. Expected node order:
             agent -> tools -> agent -> capture(attempt 1)
                   -> verify(verified=False) -> agent
                   -> capture(attempt 2) -> verify(verified=True) -> finalize
  PART B — N-PDF GROUPING: three fake PDFs (two the SAME product, one
           DIFFERENT) are each extracted by the agent, then grouped. We assert
           the two same-product docs land in one group and the odd one out in
           its own, then build the combined draft.

Records use the REAL DocRecord shape from src/schema.py: identity fields plus
a `facts` list of {field_name, value, source, quote}.
"""
import json
import sys
sys.path.insert(0, ".")

from langchain_core.messages import AIMessage  # noqa: E402
from src.agent import make_app, initial_state  # noqa: E402
from src.multi import (  # noqa: E402
    extract_record, group_records, build_multi_draft,
)


# ===========================================================================
# PART A — prove the verifier loop fires
# ===========================================================================
# Every GOOD quote is a verbatim substring of this text; the BAD one is not.
DOC = """Deye Datasheet
Document type: Datasheet
Model: SUN-5K-G06P3
Manufacturer: Ningbo Deye Inverter Technology Co Ltd
Phase: three-phase
Max DC input voltage: 1100V
Rated power: 5000 W
Ingress protection IP65
Output frequency 50/60 Hz
Standards: IEC 61727 and IEC 62116"""

GOOD = {"record": {
    "doc_type": "Datasheet",
    "model_series": "SUN-5K-G06P3",
    "phase": "three",
    "voltage_class": "1100V",
    "facts": [
        {"field_name": "manufacturer_name",
         "value": "Ningbo Deye Inverter Technology Co Ltd", "source": "deye",
         "quote": "Manufacturer: Ningbo Deye Inverter Technology Co Ltd"},
        {"field_name": "rated_power", "value": "5000 W", "source": "deye",
         "quote": "Rated power: 5000 W"},
        {"field_name": "ip_rating", "value": "IP65", "source": "deye",
         "quote": "Ingress protection IP65"},
        {"field_name": "output_frequency", "value": "50/60 Hz",
         "source": "deye", "quote": "Output frequency 50/60 Hz"},
        {"field_name": "standards", "value": "IEC 61727 and IEC 62116",
         "source": "deye", "quote": "Standards: IEC 61727 and IEC 62116"},
    ],
}}


class LoopFakeLLM:
    """Scripts three turns: search, a BAD submit, then a GOOD submit."""
    def __init__(self):
        self.i = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.i += 1
        if self.i == 1:                      # turn 1: search the document
            return AIMessage(content="", tool_calls=[
                {"name": "search_document", "args": {"query": "IEC"},
                 "id": "s1"}])
        if self.i == 2:                   # turn 2: FABRICATED quote -> fails
            bad = {"record": {"facts": [
                {"field_name": "rated_power", "value": "9999 W",
                 "source": "deye", "quote": "Rated power: 9999 W"}]}}
            return AIMessage(content="", tool_calls=[
                {"name": "submit_extraction", "id": "x1", "args": bad}])
        return AIMessage(content="", tool_calls=[   # turn 3+: the GOOD record
            {"name": "submit_extraction", "id": f"x{self.i}", "args": GOOD}])


print("=== PART A: streaming the run (watch the loop) ===")
app = make_app(LoopFakeLLM(), DOC, "deye")
for step in app.stream(initial_state(DOC, "deye")):
    for node, update in step.items():
        extra = ""
        if node == "verify":
            extra = f"  verified={update.get('verified')}"
        if node == "capture":
            extra = f"  attempt={update.get('attempts')}"
        print(f"  NODE: {node}{extra}")


# ===========================================================================
# PART B — three PDFs: two same product, one different -> grouping
# ===========================================================================
# Each doc gets its own scripted fake (search once, then submit its record).
DOC_DEYE_A = """Deye Datasheet A
Model: SUN-5K-G06P3
Phase: three-phase
Rated power: 5000 W
Ingress protection IP65
Standards: IEC 61727 and IEC 62116"""

REC_DEYE_A = {"record": {
    "doc_type": "Datasheet", "model_series": "SUN-5K-G06P3", "phase": "three",
    "voltage_class": "1100V", "facts": [
        {"field_name": "rated_power", "value": "5000 W",
         "source": "deye_a.pdf", "quote": "Rated power: 5000 W"},
        {"field_name": "ip_rating", "value": "IP65", "source": "deye_a.pdf",
         "quote": "Ingress protection IP65"},
        {"field_name": "standards", "value": "IEC 61727 and IEC 62116",
         "source": "deye_a.pdf",
         "quote": "Standards: IEC 61727 and IEC 62116"},
    ]}}

# Same product as A (shared model SUN-5K-G06P3 + same phase), different source.
DOC_DEYE_B = """Deye Test Report B
Model: SUN-5K-G06P3
Phase: three-phase
Output frequency 50/60 Hz
Ingress protection IP65
Standards: IEC 62109-1 safety"""

REC_DEYE_B = {"record": {
    "doc_type": "Test Report", "model_series": "SUN-5K-G06P3",
    "phase": "three", "voltage_class": "1100V", "facts": [
        {"field_name": "output_frequency", "value": "50/60 Hz",
         "source": "deye_b.pdf", "quote": "Output frequency 50/60 Hz"},
        {"field_name": "ip_rating", "value": "IP65", "source": "deye_b.pdf",
         "quote": "Ingress protection IP65"},
        {"field_name": "standards", "value": "IEC 62109-1",
         "source": "deye_b.pdf", "quote": "Standards: IEC 62109-1 safety"},
    ]}}

# A DIFFERENT product: CHISAGE single-phase micro -> its own group.
DOC_CHISAGE = """CHISAGE Datasheet
Model: CE-1P3001G-230-EU
Phase: single-phase
Rated power: 300W to 2000W
IP protection class IP67"""

REC_CHISAGE = {"record": {
    "doc_type": "Datasheet", "model_series": "CE-1P3001G-230-EU",
    "phase": "single", "voltage_class": "60V", "facts": [
        {"field_name": "rated_power", "value": "300W to 2000W",
         "source": "chisage.pdf", "quote": "Rated power: 300W to 2000W"},
        {"field_name": "ip_rating", "value": "IP67", "source": "chisage.pdf",
         "quote": "IP protection class IP67"},
    ]}}

DOCS = [
    (DOC_DEYE_A, "deye_a.pdf", REC_DEYE_A),
    (DOC_DEYE_B, "deye_b.pdf", REC_DEYE_B),
    (DOC_CHISAGE, "chisage.pdf", REC_CHISAGE),
]


class ScriptedLLM:
    """Search once, then submit the given record payload."""
    def __init__(self, payload):
        self.payload = payload
        self.i = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.i += 1
        if self.i == 1:
            return AIMessage(content="", tool_calls=[
                {"name": "search_document", "args": {"query": "Model"},
                 "id": "s1"}])
        return AIMessage(content="", tool_calls=[
            {"name": "submit_extraction", "id": f"x{self.i}",
             "args": self.payload}])


print("\n=== PART B: extract 3 fake PDFs, then group by product ===")
records = []
for text, src, payload in DOCS:
    record, final = extract_record(ScriptedLLM(payload), text, src)
    print(f"  extracted {src}: model_series={record.model_series} "
          f"phase={record.phase} verified={final.get('verified')}")
    records.append(record)

groups = group_records(records)
print(f"\n  -> {len(records)} records grouped into {len(groups)} product(s):")
for i, g in enumerate(groups, 1):
    models = sorted({m for r in g for m in (r.model_series or "").split(",")})
    print(f"     group {i}: {len(g)} source(s), models={models}")

# Assertions: two same-product docs together, the different one alone.
assert len(groups) == 2, f"expected 2 product groups, got {len(groups)}"
sizes = sorted(len(g) for g in groups)
assert sizes == [1, 2], f"expected group sizes [1, 2], got {sizes}"
two = next(g for g in groups if len(g) == 2)
assert all(r.phase == "three" for r in two), "the pair should be three-phase"
print("\n  ASSERTIONS PASSED: deye_a + deye_b grouped; chisage separate.")

print("\n=== PART B: combined draft ===")
checklist = json.load(open("data/nepqa_checklist.json"))
print(build_multi_draft(records, checklist))
