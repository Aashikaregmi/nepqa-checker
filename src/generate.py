"""
score each product against NEPQA and render the draft.

No LLM. The LLM already read the documents (PR2). This file only JUDGES:
for each NEPQA requirement, does the record satisfy it?
"""
import re

from .schema import DocRecord


def _standards_text(record: DocRecord) -> str:
    """Return the record's 'standards' fact value as lowercase text, or ''."""
    for f in record.facts:
        if f.field_name == "standards":
            return (f.value or "").lower()
    return ""


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


def _status_line(row: dict) -> str:
    return f"- **{row['status']}** — {row['id']}: {row['requirement']}"


def generate(deye: DocRecord, chisage: DocRecord,
             reconcile_result: dict, checklist: dict) -> str:
    """Build the full Nepal import-review draft as Markdown text."""
    lines = []

    lines.append("# Nepal Import Review Draft — Grid-Connected PV Inverter")
    lines.append("")
    lines.append("*For SunBridge Trading, to share with the Nepal import "
                 "agent. Checked against NEPQA-2025 §1.4. Draft for "
                 "review.*")
    lines.append("")

    # --- Part A: the headline (different products) ---
    lines.append("## 1. Important: the two documents describe different "
                 "products")
    lines.append("")
    lines.append(f"**Verdict:** {reconcile_result['verdict']}")
    lines.append("")
    lines.append(reconcile_result["reason"])
    lines.append("")
    ida = reconcile_result["identity"]["doc_a"]
    idb = reconcile_result["identity"]["doc_b"]
    lines.append("| Field | Document A | Document B |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| Document type | {ida['doc_type']} | {idb['doc_type']} |")
    lines.append(f"| Phase | {ida['phase']} | {idb['phase']} |")
    lines.append(f"| DC voltage class | {ida['voltage_class']} | "
                 f"{idb['voltage_class']} |")
    lines.append("")
    lines.append("These two documents share a factory but are different "
                 "product lines. They cannot be treated as one filing. Each "
                 "is scored separately against NEPQA below.")
    lines.append("")

    # --- Part B: per-product NEPQA scorecards ---
    for label, record in [("Product 1 — Deye (three-phase)", deye),
                          ("Product 2 — CHISAGE (single-phase)", chisage)]:
        lines.append(f"## 2. NEPQA §1.4 document scorecard — {label}")
        lines.append("")
        lines.append(f"Models: {record.model_series}")
        lines.append("")
        rows = score_documents(record, checklist)
        for row in rows:
            lines.append(_status_line(row))
        lines.append("")

    # --- Open questions (everything marked ASK_FACTORY, deduped) ---
    lines.append("## 3. To clarify with the factory")
    lines.append("")
    asks = set()
    for record in [deye, chisage]:
        for row in score_documents(record, checklist):
            if row["status"] in ("ASK_FACTORY", "MISSING"):
                asks.add(row["requirement"])
    for a in sorted(asks):
        lines.append(f"- {a}")
    lines.append("")
    lines.append("---")
    lines.append("*Statuses: MET = standard found in the document. "
                 "MISSING = required standard not present. "
                 "ASK_FACTORY = cannot be shown by this document type.*")

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
