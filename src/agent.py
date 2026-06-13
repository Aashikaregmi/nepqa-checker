"""
The AGENTIC version of the extraction stage, built as a LangGraph.

WHAT CHANGED FROM THE ORIGINAL PIPELINE
  Original:  extract() reads the PDF and fills DocRecord in ONE LLM call
             (src/extract.py, using instructor + google-genai)
                  -> reconcile() -> generate()
             a straight line I control step by step.

  Agentic:   the LLM now DRIVES the extraction. It is given tools (search
             the document, and a way to submit its answer), it DECIDES which
             tool to call, and a verifier LOOPS it back to try again when a
             quote can't be confirmed in the source text.
"""

import json
import os
from typing import Annotated, Optional, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.messages import (
    AIMessage, HumanMessage, SystemMessage, ToolMessage,
)

# Reuseing the real schema so the agent's output is a DocRecord, and the
# real deterministic scoring original pipeline uses.

from .schema import DocRecord
from .generate import (
    _product_label,
    _document_block,
    _technical_block,
    _labeling_block,
    _manufacturer_block,
)

# Bounding retries
MAX_ATTEMPTS = 3

# How many search_document calls the agent may make before we STOP it and force
# a structured submission. Without this, models either never submit (they loop
# the same search) or bail with a prose answer -- neither converges. Kept small
# because on Groq's free tier (8000 tokens/minute) every call eats the budget;
# force_submit reads the whole document anyway, so search is just exploration.
SEARCH_BUDGET = 2

# The hand-encoded NEPQA rubric (same file the original pipeline scores
# against).
_CHECKLIST_PATH = os.path.join("data", "nepqa_checklist.json")

_FACT_FIELDS = (
    "standards", "ip_rating", "output_frequency", "ac_output_voltage",
    "power_factor", "rated_power", "warranty",
    "manufacturer_name", "manufacturer_address",
    "certificate_or_report_number", "issue_date", "test_lab",
)


def _all_quotes(record: dict) -> list[tuple[str, str]]:
    """Pull every (label, quote) pair out of a record dict so verify() can
    confirm each one is really in the document. Mirrors the real DocRecord
    shape: a flat `facts` list, each fact carrying its own quote."""
    pairs = []
    for fact in record.get("facts", []) or []:
        quote = fact.get("quote")
        if quote:
            pairs.append((fact.get("field_name", "?"), quote))
    return pairs


def _squash_ws(s: str) -> str:
    """Collapse away ALL whitespace so quote checks survive PDF spacing noise
    (e.g. 'power (kW)' vs 'power(kW)'). Used by verify()."""
    return "".join((s or "").split())


def _search_count(messages: list) -> int:
    """How many search_document calls the agent has proposed so far. Used to
    enforce SEARCH_BUDGET so the agent can't loop searches forever."""
    n = 0
    for m in messages:
        for c in getattr(m, "tool_calls", None) or []:
            if c.get("name") == "search_document":
                n += 1
    return n


class AgentState(TypedDict):
    # document_text: the PDF text (the source of truth for verification)
    # source_name:   filename, stamped on each fact's 'source'
    # messages:      running conversation; the add_messages reducer APPENDS
    #                new messages instead of replacing the list
    # record:        the agent's submitted record (a DocRecord dump)
    # verified:      did every quote check out as a verbatim substring?
    # attempts:      how many times the agent has submitted
    document_text: str
    source_name: str
    messages: Annotated[list, add_messages]
    record: Optional[dict]
    verified: bool
    attempts: int
    forced: bool        # did the record come from the force_submit guard?


def make_app(llm, document_text: str, source_name: str = "document",
             submit_llm=None):
    """Returns a compiled LangGraph. `llm` is any chat model exposing
    .bind_tools() and .invoke() (the real ChatGroq, or the FakeLLM in
    tests). `submit_llm`, if given, is used for the forced submission -- a
    stronger model (gpt-oss-120b) produces valid tool-call JSON far more
    reliably on messy documents; falls back to `llm` when not provided."""
    submit_model = submit_llm if submit_llm is not None else llm

    @tool
    def search_document(query: str) -> str:
        """Search the inverter document for a word or phrase (an IEC number,
        'IP', 'phase', a model code, 'frequency', ...). Returns the matching
        lines so you can read the exact wording and copy a VERBATIM quote."""
        hits = []
        for i, line in enumerate(document_text.splitlines()):
            if query.lower() in line.lower():
                hits.append(f"  line {i}: {line.strip()}")
        if not hits:
            return f"No lines matched '{query}'. Try a different term."
        return f"Lines matching '{query}':\n" + "\n".join(hits[:15])

    @tool
    def submit_extraction(record: DocRecord) -> str:
        """Submit your finished extraction as a DocRecord. Call this ONCE you
        have found every field you can, each fact carrying a verbatim quote.
        Leave a field null / omit a fact if the document does not state it."""
        return "Extraction received; verifying quotes."

    search_tools = [search_document]                       # run by ToolNode

    def _bind(model, tools, **kw):
        """bind_tools with extra kwargs (tool_choice, max_tokens), but degrade
        gracefully for chat models that don't accept them -- e.g. the FakeLLM in
        tests, whose bind_tools takes only `tools`."""
        try:
            return model.bind_tools(tools, **kw)
        except TypeError:
            return model.bind_tools(tools)

    llm_with_tools = _bind(llm, search_tools + [submit_extraction],
                           max_tokens=512)

    SYSTEM = SystemMessage(content=(
        "You are an extraction agent for solar-inverter import paperwork.\n"
        "Produce a DocRecord with these identity fields if stated: doc_type, "
        "model_series, phase ('single' or 'three'), voltage_class (rough max "
        "DC input voltage, e.g. '1100V').\n"
        "ALWAYS fill model_series -- it is the product's identity. Use the "
        "model/type code(s) printed in the document (e.g. 'SUN-3K-G06P3-EU-AM2' "
        "or 'CE-1P3001G-230-EU'); if several models of one series are listed, "
        "use the first.\n"
        "Then a 'facts' list. Each fact has: field_name, value, source, "
        "quote. Use ONLY these field_name values:\n  "
        + ", ".join(_FACT_FIELDS) + ".\n"
        "RULES:\n"
        "1. Every fact MUST include a quote copied VERBATIM from the "
        "document.\n"
        "2. If the document does not state something, leave it out / null. "
        "Never guess.\n"
        "3. Use search_document to locate exact wording BEFORE quoting.\n"
        "4. Call only ONE tool per turn.\n"
        f"5. Always set each fact's source to '{source_name}'.\n"
        "6. When done, call submit_extraction with the full record."
    ))

    # NODES
    def agent(state: AgentState) -> dict:
        """The brain: looks at the conversation and decides the next tool
        call. Prepends the system message for the LLM call without storing it
        in state (keeps the running transcript clean)."""
        msgs = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in msgs):
            msgs = [SYSTEM] + msgs
        response = llm_with_tools.invoke(msgs)
        return {"messages": [response]}

    def force_submit(state: AgentState) -> dict:
        """Convergence guard. Reached when the agent has spent its search budget
        or answered with no tool call. Re-invokes with ONLY submit_extraction
        bound (tool_choice pinned), so the model MUST turn the document into a
        DocRecord instead of searching forever or replying in prose.

        Uses a CLEAN, minimal context -- the system rules plus the full document
        plus an explicit 'submit now' instruction -- NOT the long search
        transcript. Everything needed is already in the document text, and a
        lean prompt keeps the forced tool call reliable. (The model still quotes
        verbatim from the text below, so verify() passes.)"""
        msgs = [SYSTEM, HumanMessage(content=(
            f"Here is the full document (source: {state['source_name']}):\n\n"
            f"{state['document_text']}\n\n"
            "Call submit_extraction now with the complete DocRecord. Always "
            "fill model_series with the product's model/type code from the text "
            "(use the first if several are listed). Include every field the "
            "document states, each fact carrying a quote copied VERBATIM from "
            "the text above. Omit fields it does not state."))]
        # gpt-oss occasionally emits malformed tool-call JSON (double-encoded
        # args, stray quotes) on messy documents -> Groq 400s. Tiered retry: try
        # the cheap primary model first (deterministic, then a warmer sample),
        # and only escalate to the stronger submit_model if the primary can't
        # produce a valid record. Escalating rarely keeps the stronger model's
        # tighter free-tier rate limit off the common path.
        tiers = [(llm, 0.0), (llm, 0.6),
                 (submit_model, 0.0), (submit_model, 0.6)]
        for model, temp in tiers:
            binder = _bind(model, [submit_extraction],
                           tool_choice="submit_extraction",
                           max_tokens=3000, temperature=temp)
            try:
                response = binder.invoke(msgs)
                if getattr(response, "tool_calls", None):
                    return {"messages": [response], "forced": True}
            except Exception:
                continue
        # Last resort: an empty record, so the graph still finalizes (the draft
        # will flag everything as missing for this source) instead of crashing
        # the whole batch on one stubborn document.
        return {"messages": [AIMessage(content="", tool_calls=[{
            "name": "submit_extraction", "id": "forced_fallback",
            "args": {"record": {"facts": []}}}])], "forced": True}

    def capture(state: AgentState) -> dict:
        """Runs when the agent calls submit_extraction. Pulls the record out
        of the tool call, validates it against the REAL DocRecord schema, and
        ANSWERS the tool call -- every tool_call id needs a matching
        ToolMessage or the next LLM turn errors."""
        last = state["messages"][-1]
        call = next(c for c in last.tool_calls
                    if c["name"] == "submit_extraction")
        args = call["args"]
        payload = args.get("record", args) if isinstance(args, dict) else args
        try:
            record = DocRecord(**payload).model_dump()
            note = "Record received; verifying quotes."
        except Exception as e:               # schema didn't fit -> tell agent
            return {
                "messages": [ToolMessage(
                    content=f"Invalid record: {e}. Please fix and resubmit.",
                    tool_call_id=call["id"])],
                "record": None,
                "verified": False,
                "attempts": state.get("attempts", 0) + 1,
            }
        return {
            "messages": [ToolMessage(content=note, tool_call_id=call["id"])],
            "record": record,
            "attempts": state.get("attempts", 0) + 1,
        }

    def verify(state: AgentState) -> dict:
        """DETERMINISTIC guardrail: a model can fake a quote, but it cannot
        fake the document containing it. Check each quote appears in
        document_text; if any fail, list them for the agent.

        Comparison is whitespace-insensitive: PDF table extraction is noisy
        about spaces (e.g. 'power (kW)' vs 'power(kW)'), so we strip ALL
        whitespace from both sides before the substring check. This still
        catches a fabricated quote -- its non-space characters won't appear in
        the source -- while tolerating spacing artifacts the model can't help."""
        record = state.get("record")
        if not record:
            return {"verified": False}
        haystack = _squash_ws(state["document_text"])
        bad = [label for label, quote in _all_quotes(record)
               if _squash_ws(quote) not in haystack]
        if not bad:
            return {"verified": True}
        msg = ("These quotes were NOT found verbatim in the document: "
               + "; ".join(bad)
               + ". Re-read those parts with search_document and resubmit "
                 "with exact quotes.")
        return {"verified": False, "messages": [HumanMessage(content=msg)]}

    def finalize(state: AgentState) -> dict:
        """DETERMINISTIC verdict -- the reconcile/generate territory. Reuses
        the REAL scoring/formatting from src/generate.py (the block builders
        call score_documents / score_technical under the hood) so the pass/
        fail logic is identical to the original pipeline and fully auditable.

        Single-PDF run: scores ONE record against NEPQA. The cross-document
        comparison (real reconcile + generate over MANY records) lives in
        src/multi.py and is what run_agent.py uses."""
        checklist = json.load(open(_CHECKLIST_PATH))
        record = DocRecord(**(state["record"] or {}))
        label = _product_label(record)

        lines = ["# NEPQA Import-Review Draft (agentic extraction)", "",
                 f"*Source: {state['source_name']}. Checked against "
                 f"NEPQA-2025 §1.4. Draft for review.*", ""]
        if not state.get("verified", False):
            lines.append(
                "> NOTE: quote verification did not fully pass after "
                f"{state.get('attempts', 0)} attempts — review the flagged "
                "fields before relying on this draft.\n")
        # Reuse the real generate.py block builders (the deterministic
        # verdict).
        lines.extend(_document_block(label, record, checklist))
        lines.extend(_technical_block(label, record, checklist))
        lines.extend(_labeling_block(label, record, checklist))
        lines.extend(_manufacturer_block(label, record))
        draft = "\n".join(lines)
        return {"messages": [AIMessage(content=draft)]}

    # ROUTERS
    def route_after_agent(state: AgentState) -> str:
        last = state["messages"][-1]
        calls = getattr(last, "tool_calls", None) or []
        if any(c["name"] == "submit_extraction" for c in calls):
            return "capture"
        # Still has search budget and wants to search -> run the tool.
        if calls and _search_count(state["messages"]) <= SEARCH_BUDGET:
            return "tools"
        return "force_submit"

    def route_after_verify(state: AgentState) -> str:
        if (state.get("verified") or state.get("forced")
                or state.get("attempts", 0) >= MAX_ATTEMPTS):
            return "finalize"
        return "agent"

    # GRAPH WIRING
    g = StateGraph(AgentState)
    g.add_node("agent", agent)
    g.add_node("force_submit", force_submit)
    g.add_node("tools", ToolNode(search_tools))
    g.add_node("capture", capture)
    g.add_node("verify", verify)
    g.add_node("finalize", finalize)

    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route_after_agent,
                            {"tools": "tools", "capture": "capture",
                             "force_submit": "force_submit"})
    g.add_edge("force_submit", "capture")         # forced record -> validate it
    g.add_edge("tools", "agent")
    g.add_edge("capture", "verify")
    g.add_conditional_edges("verify", route_after_verify,
                            {"agent": "agent", "finalize": "finalize"})
    g.add_edge("finalize", END)

    return g.compile()


def initial_state(document_text: str, source_name: str) -> AgentState:
    # NOTE: we deliberately do NOT inline the full document in the opening
    # message. The agent has search_document for that, and re-sending the whole
    # PDF on every turn would blow Groq's free-tier token budget. The full text
    # still lives in state['document_text'] -- search_document reads it, verify()
    # checks quotes against it, and force_submit feeds it in once at the end.
    return {
        "document_text": document_text,
        "source_name": source_name,
        "messages": [HumanMessage(content=(
            f"Extract the inverter details from the document "
            f"'{source_name}'. Use search_document to find the exact wording "
            "for the fields you need (standards, IP rating, output frequency, "
            "AC output voltage, power factor, rated power, warranty, "
            "manufacturer, certificate/report number, issue date, test lab), "
            "then call submit_extraction with a verbatim quote for each fact."
        ))],
        "record": None,
        "verified": False,
        "attempts": 0,
        "forced": False,
    }
