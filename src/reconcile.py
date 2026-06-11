"""
compare two or more DocRecords with plain Python.

No LLM here. This is the deterministic judge. It first decides whether the
records describe the SAME product or DIFFERENT products (identity check),
then either compares their facts or marks everything out-of-scope.
"""
from .schema import DocRecord


def _normalize(value: str | None) -> str:
    """Lowercase, drop all whitespace, and unify full-width punctuation,
    so '50Hz' vs '50 Hz' or 'IP65' vs 'IP 65' are not false conflicts."""
    if not value:
        return ""
    text = value.lower()
    for full, ascii_ in (("＞", ">"), ("＜", "<"), ("％", "%"),
                         ("～", "~"), ("：", ":")):
        text = text.replace(full, ascii_)
    return "".join(text.split())


def _models(record: DocRecord) -> set[str]:
    """Split the model_series string into a set of individual model names."""
    if not record.model_series:
        return set()
    return {m.strip() for m in record.model_series.split(",") if m.strip()}


def same_product(a: DocRecord, b: DocRecord) -> bool:
    """
    Decide if two records describe the same product.
    Rule: they must share at least one model AND agree on phase.
    """
    shared_models = _models(a) & _models(b)
    same_phase = (a.phase or "").lower() == (b.phase or "").lower()
    return bool(shared_models) and same_phase


def reconcile(a: DocRecord, b: DocRecord) -> dict:
    """
    Compare two records and return a decision dictionary.
    """
    if not same_product(a, b):
        return {
            "verdict": "DIFFERENT_PRODUCT",
            "reason": (
                "Records do not share any model number and/or differ "
                "in phase. Their specifications are not comparable."
            ),
            "identity": {
                "doc_a": {"doc_type": a.doc_type, "phase": a.phase,
                          "voltage_class": a.voltage_class},
                "doc_b": {"doc_type": b.doc_type, "phase": b.phase,
                          "voltage_class": b.voltage_class},
            },
            "rows": [],
        }

    # --- same product: compare facts field by field ---
    facts_a = {f.field_name: f for f in a.facts}
    facts_b = {f.field_name: f for f in b.facts}
    all_fields = sorted(set(facts_a) | set(facts_b))

    rows = []
    for field in all_fields:
        fa, fb = facts_a.get(field), facts_b.get(field)
        if fa and fb:
            if _normalize(fa.value) == _normalize(fb.value):
                status = "CONFIRMED"
            else:
                status = "CONFLICT"
        else:
            status = "PENDING"  # only one source has it
        rows.append({
            "field": field,
            "value_a": fa.value if fa else None,
            "value_b": fb.value if fb else None,
            "status": status,
        })

    return {
        "verdict": "SAME_PRODUCT",
        "reason": "",
        "identity": {},
        "rows": rows,
    }
