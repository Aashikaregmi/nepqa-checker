"""
Generalize the agentic pipeline from "exactly two PDFs" to N PDFs.

Same principle, scaled up: AGENTIC for extraction, DETERMINISTIC for the
verdict. The flow for many documents is:

    extract each PDF (agentic, fan-out)   -- run the agent graph once per file
        -> GROUP by product (deterministic)
        -> reconcile WITHIN each group (deterministic)
        -> one combined draft (deterministic, reuses src/generate.py)

THE KEY DESIGN CHOICE -- group before reconciling:
    So we first CLUSTER the records by product
    using the SAME same-product rule already in reconcile.py (shared model
    number + matching phase), then only reconcile within a cluster. Different
    products never get compared to each other.
"""

from .schema import DocRecord
from .reconcile import same_product, reconcile
from .generate import (
    _product_label,
    _document_block,
    _technical_block,
    _labeling_block,
    _manufacturer_block,
)


def extract_record(llm, document_text: str, source_name: str,
                   submit_llm=None):
    """Run the agent graph once for one document and return (DocRecord, final
    state). Reused by both run_agent.py (real Groq llm) and test_wiring.py
    (fake llm), so the fan-out logic is written once. `submit_llm` (optional) is
    the stronger model used for the forced submission.
"""

    from .agent import make_app, initial_state
    app = make_app(llm, document_text, source_name, submit_llm=submit_llm)
    # recursion_limit headroom: search budget + the verify/retry loop can take
    # ~20-30 graph steps
    final = app.invoke(initial_state(document_text, source_name),
                       {"recursion_limit": 50})
    record = DocRecord(**(final.get("record") or {}))
    return record, final


def group_records(records: list[DocRecord]) -> list[list[DocRecord]]:
    """Cluster records by PRODUCT using reconcile.same_product (shared,
    normalized model number + matching phase).

    Greedy, order-stable: each record joins the first existing group whose
    REPRESENTATIVE (its first member) is the same product; otherwise it starts
    a new group. Records that match nothing form their own group of one.
"""
    groups: list[list[DocRecord]] = []
    for rec in records:
        placed = False
        for group in groups:
            if same_product(group[0], rec):  # compare to the representative
                group.append(rec)
                placed = True
                break
        if not placed:
            groups.append([rec])
    return groups


# helpers 
def _record_sources(record: DocRecord) -> set[str]:
    """The source filename(s) behind a record -- read off its facts, since
    every fact carries the source the agent stamped on it."""
    return {f.source for f in record.facts if f.source}


def _group_sources(group: list[DocRecord]) -> list[str]:
    """All distinct source filenames in a group, sorted for stable output."""
    out: set[str] = set()
    for rec in group:
        out |= _record_sources(rec)
    return sorted(out) or ["(unknown source)"]


def _within_group_block(group: list[DocRecord]) -> list[str]:
    """Cross-check the sources INSIDE one product group using the real reconcile()."""
    lines = ["**Within-group consistency** "
             "(same product — cross-checked across its sources):", ""]
    rep = group[0]
    rep_src = ", ".join(sorted(_record_sources(rep))) or "source A"
    for other in group[1:]:
        other_src = ", ".join(sorted(_record_sources(other))) or "source B"
        result = reconcile(rep, other)       # <- existing deterministic logic
        lines.append(f"Comparing **{rep_src}** vs **{other_src}**:")
        lines.append("")
        lines.append("| Field | A | B | Status |")
        lines.append("| --- | --- | --- | --- |")
        for row in result["rows"]:
            va = row["value_a"] or "—"
            vb = row["value_b"] or "—"
            lines.append(f"| {row['field']} | {va} | {vb} | "
                         f"{row['status']} |")
        lines.append("")
    return lines


# COMBINED DRAFT
def build_multi_draft(records: list[DocRecord], checklist: dict) -> str:
    """Group N records by product and write one draft: each product group, the
    sources in it, within-group agreements/conflicts, and the NEPQA checklist
    score (reusing the real generate.py block builders).

    Works for any N: N=1 -> one single-source product; N=2 same product -> one
    group with a comparison; mixed products -> one group each, clearly flagged
    as different and never cross-compared."""
    groups = group_records(records)

    lines = ["# Nepal Import Review Draft — Grid-Connected PV Inverter "
             "(multi-source)", ""]
    lines.append(f"*{len(records)} source document(s), {len(groups)} product "
                 "group(s). Checked against NEPQA-2025 §1.4. Draft for "
                 "review.*")
    lines.append("")

    if len(groups) > 1:
        lines.append(f"## Important: these sources describe {len(groups)} "
                     "DIFFERENT products")
        lines.append("")
        lines.append("They are grouped by model number + phase and scored "
                     "separately below. Sources in different groups are NOT "
                     "compared to each other — that would invent false "
                     "conflicts between unrelated products.")
        lines.append("")

    for idx, group in enumerate(groups, 1):
        rep = group[0]                  # representative record for the group
        label = _product_label(rep)
        lines.append(f"## Product {idx}: {label}")
        lines.append("")
        lines.append(f"Sources ({len(group)}): "
                     f"{', '.join(_group_sources(group))}")
        lines.append("")

        if len(group) >= 2:
            lines.extend(_within_group_block(group))
        else:
            lines.append("_Single source — no cross-source comparison._")
            lines.append("")

        # NEPQA checklist score, reusing the real generate.py block builders
        lines.append(f"### NEPQA score — {label}")
        lines.append("")
        lines.extend(_document_block(label, rep, checklist))
        lines.extend(_technical_block(label, rep, checklist))
        lines.extend(_labeling_block(label, rep, checklist))
        lines.extend(_manufacturer_block(label, rep))

    return "\n".join(lines)
