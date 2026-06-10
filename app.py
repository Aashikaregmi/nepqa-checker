import json
import os
import tempfile

import streamlit as st

from src.schema import DocRecord
from src.extract import extract
from src.reconcile import reconcile
from src.generate import generate

st.title("NEPQA Inverter Paperwork Checker")
st.write(
    "Upload the manufacturer PDFs. The tool reads each one, compares them, "
    "and produces a draft checked against NEPQA-2025 §1.4."
)

checklist = json.load(open("data/nepqa_checklist.json"))

use_saved = st.checkbox(
    "Use already-saved records (no API calls)", value=True,
    help="Leave on to reuse output/*.json. Turn off to extract live (uses Gemini quota).",
)

uploaded = st.file_uploader(
    "Manufacturer PDFs", type="pdf", accept_multiple_files=True,
)

if st.button("Run pipeline"):
    records = []

    if use_saved:
        st.write("Loading saved records from output/...")
        for name in ["deye_record.json", "chisage_record.json"]:
            path = os.path.join("output", name)
            records.append(DocRecord(**json.load(open(path))))
    else:
        if not uploaded:
            st.error("Upload at least one PDF, or tick 'Use already-saved records'.")
            st.stop()
        for f in uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(f.getbuffer())
                tmp_path = tmp.name
            st.write(f"Extracting {f.name} ...")
            records.append(extract(tmp_path))

    if len(records) < 2:
        st.warning("Need two records to compare. Using what is available.")

    # show each record's facts
    for r in records:
        with st.expander(f"Extracted: {r.doc_type} ({r.phase}-phase)"):
            st.json(r.model_dump())

    # reconcile + generate (assumes first two records)
    deye, chisage = records[0], records[1]
    result = reconcile(deye, chisage)
    draft = generate(deye, chisage, result, checklist)

    st.subheader("Draft")
    st.markdown(draft)
    st.download_button("Download draft.md", draft, file_name="draft.md")

    from src.generate import draft_to_pdf
    pdf_bytes = draft_to_pdf(draft)
    st.download_button(
        "Download draft.pdf", pdf_bytes,
        file_name="draft.pdf", mime="application/pdf",
    )