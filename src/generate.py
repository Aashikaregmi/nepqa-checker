"""
score each product against NEPQA and render the draft.

No LLM. The LLM already read the documents (PR2). This file only JUDGES:
for each NEPQA requirement, does the record satisfy it? It produces the
document scorecard, the technical scorecard, the labeling pre-fill, and the
manufacturer/test-information section, then renders everything as Markdown.
"""
import re

from .schema import DocRecord


# --- small fact helpers --------------------------------------------------

def _fact(record: DocRecord, field_name: str):
    """Return the Fact with this field_name, or None."""
    for f in record.facts:
        if f.field_name == field_name:
            return f
    return None


def _fact_value(record: DocRecord, field_name: str) -> str | None:
    """Return the value of a named fact, or None if absent."""
    f = _fact(record, field_name)
    return f.value if f else None


def _product_label(record: DocRecord) -> str:
    """Derive a product label from the record itself (first model + phase),
    so the draft is correct regardless of upload order."""
    first_model = (record.model_series or "").split(",")[0].strip()
    first_model = first_model or "unknown model"
    phase = f"{record.phase}-phase" if record.phase else "phase unknown"
    return f"{first_model} ({phase})"


# --- document scorecard --------------------------------------------------

def _standards_text(record: DocRecord) -> str:
    """Return the record's 'standards' fact value as lowercase text, or ''."""
    return (_fact_value(record, "standards") or "").lower()


def _standard_numbers(requirement_text: str) -> list[str]:
    """Find IEC standard tokens like '61727' or '62109-1' in a line."""
    return re.findall(r"\b(\d{5}(?:-\d)?)\b", requirement_text)


def score_documents(record: DocRecord, checklist: dict) -> list[dict]:
    """Score only the 'required_documents' that name an IEC standard."""
    standards = _standards_text(record)
    results = []
    for item in checklist["required_documents"]:
        numbers = _standard_numbers(item["requirement"])
        if not numbers:
            status = "ASK_FACTORY"   # e.g. warranty agreement, datasheet
        elif all(n in standards for n in numbers):
            status = "MET"           # all named standards present
        else:
            status = "MISSING"
        results.append({
            "id": item["id"],
            "requirement": item["requirement"],
            "status": status,
        })
    return results


# --- technical scorecard -------------------------------------------------

# TECH items that map to a fact we actually extract. Everything else is
# NOT_STATED (not in this document — await the test reports).
_TECH_FIELD = {
    "TECH-1": "ac_output_voltage",
    "TECH-2": "output_frequency",
    "TECH-10": "power_factor",
    "TECH-11": "ip_rating",
}


def _judge_tech(tech_id: str, value: str) -> str:
    """Judge one technical requirement against a stated value. Never guesses;
    returns MET or FAIL only for the few TECH items we can actually check."""
    v = value.lower().replace("＞", ">").replace("～", "~")
    v = "".join(v.split())
    if tech_id == "TECH-1":   # 3-ph 400V or 1-ph 230V (±10%)
        return "MET" if ("230" in v or "400" in v) else "FAIL"
    if tech_id == "TECH-2":   # 50Hz ±2.5% ("50/60 Hz" counts: 50 supported)
        return "MET" if "50" in v else "FAIL"
    if tech_id == "TECH-10":  # PF >0.99 nominal, adjustable 0.8 lead–lag
        if "0.99" in v or "unity" in v or "leading" in v:
            return "MET"
        return "FAIL"
    if tech_id == "TECH-11":  # ingress protection >= IP65
        m = re.search(r"ip(\d{2})", v)
        return "MET" if (m and int(m.group(1)) >= 65) else "FAIL"
    return "NOT_STATED"


def score_technical(record: DocRecord, checklist: dict) -> list[dict]:
    """Score the technical_requirements we can check from extracted facts.

    Only TECH items mapped in _TECH_FIELD are judged; the rest are
    NOT_STATED. Each judged row carries the extracted value and its quote
    so the agent can verify provenance."""
    results = []
    for item in checklist["technical_requirements"]:
        field = _TECH_FIELD.get(item["id"])
        fact = _fact(record, field) if field else None
        if fact is None or not fact.value:
            status, value, quote = "NOT_STATED", None, None
        else:
            status = _judge_tech(item["id"], fact.value)
            value, quote = fact.value, fact.quote
        results.append({
            "id": item["id"],
            "requirement": item["requirement"],
            "status": status,
            "value": value,
            "quote": quote,
        })
    return results


# --- labeling pre-fill (informational, not pass/fail) --------------------

def label_prefill(record: DocRecord, checklist: dict) -> list[dict]:
    """For each NEPQA label field, what we can pre-fill from extracted facts.

    There is no label artwork or photo, so this is informational only."""
    voltage = _fact_value(record, "ac_output_voltage")
    freq = _fact_value(record, "output_frequency")
    if voltage and freq:
        volt_freq = f"{voltage}, {freq}"
    else:
        volt_freq = voltage or freq
    prefill = {
        "LBL-1": _fact_value(record, "manufacturer_name"),
        "LBL-2": record.model_series,
        "LBL-3": _fact_value(record, "rated_power"),
        "LBL-4": volt_freq,
        "LBL-5": record.voltage_class,
        "LBL-6": None,   # MPPT voltage range — not extracted
        "LBL-7": None,   # serial number — per-unit, not in these docs
    }
    results = []
    for item in checklist["label_fields"]:
        results.append({
            "id": item["id"],
            "requirement": item["requirement"],
            "value": prefill.get(item["id"]),
        })
    return results


# --- markdown block builders --------------------------------------------

def _status_line(row: dict) -> str:
    return f"- **{row['status']}** — {row['id']}: {row['requirement']}"


def _tech_line(row: dict) -> str:
    line = f"- **{row['status']}** — {row['id']}: {row['requirement']}"
    if row["value"]:
        line += f"\n  - extracted: {row['value']}"
        if row["quote"]:
            quote = row["quote"].replace("\n", " ").strip()
            line += f' (quote: "{quote}")'
    return line


def _facts_reference_table(a: DocRecord, b: DocRecord) -> list[str]:
    """Side-by-side reference table of both records' facts (not a conflict
    comparison — these are different products)."""
    facts_a = {f.field_name: f for f in a.facts}
    facts_b = {f.field_name: f for f in b.facts}
    fields = sorted(set(facts_a) | set(facts_b))
    lines = ["| Field | Value (A) | Value (B) | Sources |",
             "| --- | --- | --- | --- |"]
    for field in fields:
        fa, fb = facts_a.get(field), facts_b.get(field)
        va = (fa.value if fa else None) or "—"
        vb = (fb.value if fb else None) or "—"
        src = " / ".join(sorted({
            f.source for f in (fa, fb) if f and f.source
        })) or "—"
        va = va.replace("\n", " ")
        vb = vb.replace("\n", " ")
        lines.append(f"| {field} | {va} | {vb} | {src} |")
    return lines


def _document_block(label: str, record: DocRecord,
                    checklist: dict) -> list[str]:
    lines = [f"## NEPQA §1.4 document scorecard — {label}", "",
             f"Models: {record.model_series}", ""]
    for row in score_documents(record, checklist):
        lines.append(_status_line(row))
    lines.append("")
    return lines


def _technical_block(label: str, record: DocRecord,
                     checklist: dict) -> list[str]:
    lines = [f"## NEPQA §1.4 technical scorecard — {label}", ""]
    for row in score_technical(record, checklist):
        lines.append(_tech_line(row))
    lines.append("")
    return lines


def _labeling_block(label: str, record: DocRecord,
                    checklist: dict) -> list[str]:
    lines = [f"## Labeling — {label}", "",
             "No label artwork or photo provided — pending from factory. "
             "What we could pre-fill from the extracted facts:", ""]
    for row in label_prefill(record, checklist):
        value = row["value"] or "unknown — pending from factory"
        value = value.replace("\n", " ")
        lines.append(f"- {row['id']} ({row['requirement']}): {value}")
    lines.append("")
    return lines


def _manufacturer_block(label: str, record: DocRecord) -> list[str]:
    lines = [f"## Manufacturer and test information — {label}", ""]
    fields = [
        ("Manufacturer", "manufacturer_name"),
        ("Manufacturer address", "manufacturer_address"),
        ("Certificate / report number", "certificate_or_report_number"),
        ("Issue date", "issue_date"),
        ("Test lab / issuing body", "test_lab"),
    ]
    for title, field_name in fields:
        value = _fact_value(record, field_name) or "not stated in document"
        value = value.replace("\n", " ")
        lines.append(f"- {title}: {value}")
    lines.append("")
    return lines


def _clarify_block(records: list[DocRecord], checklist: dict) -> list[str]:
    """Everything marked MISSING / ASK_FACTORY across products, deduped."""
    lines = ["## To clarify with the factory", ""]
    asks = set()
    for record in records:
        for row in score_documents(record, checklist):
            if row["status"] in ("ASK_FACTORY", "MISSING"):
                asks.add(row["requirement"])
    for a in sorted(asks):
        lines.append(f"- {a}")
    lines.append("")
    return lines


def generate(record_a: DocRecord, record_b: DocRecord,
             reconcile_result: dict, checklist: dict) -> str:
    """Build the full Nepal import-review draft as Markdown text.

    Product labels are derived from each record, so upload order does not
    matter. When the records describe different products, a side-by-side
    reference table of their facts is included (clearly not a conflict)."""
    label_a = _product_label(record_a)
    label_b = _product_label(record_b)

    lines = []
    lines.append("# Nepal Import Review Draft — Grid-Connected PV Inverter")
    lines.append("")
    lines.append("*For SunBridge Trading, to share with the Nepal import "
                 "agent. Checked against NEPQA-2025 §1.4. Draft for "
                 "review.*")
    lines.append("")

    # --- 1. Identity / verdict ---
    different = reconcile_result["verdict"] == "DIFFERENT_PRODUCT"
    if different:
        lines.append("## 1. Important: the two documents describe different "
                     "products")
    else:
        lines.append("## 1. Identity check")
    lines.append("")
    lines.append(f"**Verdict:** {reconcile_result['verdict']}")
    lines.append("")
    if reconcile_result["reason"]:
        lines.append(reconcile_result["reason"])
        lines.append("")

    if different:
        ida = reconcile_result["identity"]["doc_a"]
        idb = reconcile_result["identity"]["doc_b"]
        lines.append(f"| Field | {label_a} | {label_b} |")
        lines.append("| --- | --- | --- |")
        lines.append(f"| Document type | {ida['doc_type']} | "
                     f"{idb['doc_type']} |")
        lines.append(f"| Phase | {ida['phase']} | {idb['phase']} |")
        lines.append(f"| DC voltage class | {ida['voltage_class']} | "
                     f"{idb['voltage_class']} |")
        lines.append("")
        lines.append("These two documents share a factory but are different "
                     "product lines. They cannot be treated as one filing. "
                     "Each is scored separately against NEPQA below.")
        lines.append("")
        lines.append("**Extracted facts, for reference — these are different "
                     "products, not a conflict comparison:**")
        lines.append("")
        lines.extend(_facts_reference_table(record_a, record_b))
        lines.append("")

    # --- per-product scorecards ---
    for label, record in [(label_a, record_a), (label_b, record_b)]:
        lines.extend(_document_block(label, record, checklist))
        lines.extend(_technical_block(label, record, checklist))
        lines.extend(_labeling_block(label, record, checklist))
        lines.extend(_manufacturer_block(label, record))

    # --- to clarify with the factory ---
    lines.extend(_clarify_block([record_a, record_b], checklist))

    lines.append("---")
    lines.append("*Statuses — documents: MET = standard found; MISSING = "
                 "required standard not present; ASK_FACTORY = cannot be "
                 "shown by this document type. Technical: MET/FAIL = checked "
                 "against the extracted value; NOT_STATED = not in this "
                 "document, await test reports.*")

    return "\n".join(lines)


def draft_to_pdf(draft_text: str) -> bytes:
    """Convert the draft markdown text into a simple PDF (bytes)."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in draft_text.split("\n"):
        stripped = line.strip()
        # skip pure markdown separators (table rule and horizontal rule)
        if set(stripped) <= {"-", "|", " "} and "-" in stripped:
            continue
        # strip markdown markers for clean plain-text output
        clean = stripped.replace("#", "").replace("**", "").replace("*", "")
        clean = clean.replace("|", " ").replace("—", "-").strip()
        # core Helvetica is latin-1 only; drop anything it can't encode
        clean = clean.encode("latin-1", "replace").decode("latin-1")
        if clean == "":
            pdf.ln(4)
        else:
            pdf.multi_cell(0, 6, clean,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return bytes(pdf.output())
