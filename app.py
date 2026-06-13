import json
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from src.schema import DocRecord
from src.generate import _product_label, draft_to_pdf
from src.multi import extract_record, build_multi_draft

# Reuse the CLI's PDF reader so the UI normalizes text exactly like run_agent.py.
from run_agent import read_pdf, GROQ_MODEL, SUBMIT_MODEL

load_dotenv()

st.title("NEPQA Inverter Paperwork Checker")
st.write(
    "Upload the manufacturer PDFs. A **LangGraph agent** (Groq "
    f"`{GROQ_MODEL}`) reads each one — searching the document and "
    "self-correcting through a quote verifier — then deterministic Python "
    "groups, reconciles, and scores them against NEPQA-2025 §1.4."
)

checklist = json.load(open("data/nepqa_checklist.json"))

use_saved = st.checkbox(
    "Use already-saved records (no API calls)", value=True,
    help="Leave on for an instant demo from output/*.json. Turn off to run "
         "the agentic extraction live (uses your Groq free-tier quota).",
)

uploaded = st.file_uploader(
    "Manufacturer PDFs", type="pdf", accept_multiple_files=True,
)


@st.cache_resource(show_spinner=False)
def get_llms():
    """Build the Groq chat models once (cached across reruns). Same config as
    run_agent.py: temperature 0 for deterministic extraction, low reasoning so
    the forced submit leaves room for the tool call, and retries so a brief
    free-tier rate limit backs off instead of crashing. The 20b model runs the
    cheap search turns; the 120b model handles the forced submission, where
    valid tool-call JSON matters most."""
    from langchain_groq import ChatGroq
    common = dict(temperature=0, reasoning_effort="low", max_retries=5)
    llm = ChatGroq(model=GROQ_MODEL, **common)
    submit_llm = ChatGroq(model=SUBMIT_MODEL, **common)
    return llm, submit_llm


def _label(record: DocRecord) -> str:
    """Friendly product label for the expander header."""
    try:
        return _product_label(record)
    except Exception:
        return record.doc_type or "record"


if st.button("Run pipeline"):
    records = []

    if use_saved:
        st.write("Loading saved records from output/ ...")
        for name in ["deye_record.json", "chisage_record.json"]:
            path = os.path.join("output", name)
            records.append(DocRecord(**json.load(open(path))))
    else:
        if not uploaded:
            st.error("Upload at least one PDF, or tick "
                     "'Use already-saved records'.")
            st.stop()
        if not os.getenv("GROQ_API_KEY"):
            st.error("Set GROQ_API_KEY in your .env file "
                     "(https://console.groq.com/keys) to run live.")
            st.stop()

        llm, submit_llm = get_llms()
        for f in uploaded:
            with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf") as tmp:
                tmp.write(f.getbuffer())
                tmp_path = tmp.name
            with st.status(f"Agentic extraction: {f.name}",
                           expanded=False) as status:
                doc_text = read_pdf(tmp_path)
                try:
                    record, final = extract_record(
                        llm, doc_text, f.name, submit_llm=submit_llm)
                except Exception as e:
                    status.update(
                        label=f"{f.name} — extraction failed, skipped",
                        state="error")
                    st.warning(f"{f.name}: extraction failed ({e}). Skipped.")
                    continue
                # An empty record (no facts) means the agent could not produce a
                # valid extraction -- skip it rather than render a blank record.
                if not record.facts:
                    status.update(
                        label=f"{f.name} — no facts extracted, skipped",
                        state="error")
                    st.warning(
                        f"{f.name}: the model could not extract any facts "
                        "(it failed to return a valid record). Skipped — try "
                        "running again.")
                    continue
                verified = final.get("verified")
                attempts = final.get("attempts")
                status.update(
                    label=f"{f.name} — quotes verified: {verified} "
                          f"(attempts: {attempts})",
                    state="complete")
            records.append(record)

    if not records:
        st.warning("No records could be extracted.")
        st.stop()

    # Show each record's extracted facts.
    for r in records:
        with st.expander(f"Extracted: {_label(r)}"):
            st.json(r.model_dump())

    # Group by product, reconcile within each group, score against NEPQA --
    # all deterministic, reusing src/generate.py. Handles 1..N documents.
    draft = build_multi_draft(records, checklist)

    st.subheader("Draft")
    st.markdown(draft)
    st.download_button("Download draft.md", draft, file_name="draft.md")

    pdf_bytes = draft_to_pdf(draft)
    st.download_button(
        "Download draft.pdf", pdf_bytes,
        file_name="draft.pdf", mime="application/pdf",
    )
