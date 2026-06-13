"""
  (agentic for extraction, deterministic for the verdict):
  pdfplumber pulls each PDF's text  ->  a LangGraph agent (Groq Llama)
  extracts one DocRecord per file by searching + self-correcting through a
  verifier loop  ->  deterministic Python GROUPS the records by product,
  RECONCILES within each group, and writes output/draft.md (reusing
  src/generate.py scoring). The agent only replaces EXTRACTION;
  grouping/reconcile/scoring stay deterministic and auditable.
"""

import json
import os
import sys
import unicodedata

import pdfplumber
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.multi import extract_record, group_records, build_multi_draft

# Model names change over time - check https://console.groq.com/docs/models
# gpt-oss-20b is fast/cheap for the search turns; gpt-oss-120b is used only for
# the forced submission, where valid tool-call JSON matters most (the 20b model
# sometimes emits malformed JSON on messy documents).
GROQ_MODEL = "openai/gpt-oss-20b"
SUBMIT_MODEL = "openai/gpt-oss-120b"


def read_pdf(path: str, max_pages: int | None = 12) -> str:
    """Same text-extraction approach as src/extract.read_pdf_text."""
    text = []
    with pdfplumber.open(path) as pdf:
        pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
        for page in pages:
            text.append(page.extract_text() or "")
    # NFKC-normalize: PDFs carry fullwidth/odd Unicode (e.g. '＞' U+FF1E instead
    # of '>') that both derails the model's JSON and breaks verbatim quote
    # matching. Normalizing to plain ASCII-ish forms keeps both honest.
    return unicodedata.normalize("NFKC", "\n".join(text))


def collect_pdf_paths(args: list[str]) -> list[str]:
    """Accept a folder (use every *.pdf in it) or one/more file paths."""
    if len(args) == 1 and os.path.isdir(args[0]):
        folder = args[0]
        pdfs = sorted(
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.lower().endswith(".pdf")
        )
        return pdfs
    return args


def main():
    if len(sys.argv) < 2:
        print("usage: python3 run_agent.py <pdf> [<pdf> ...]  |  <folder>")
        sys.exit(1)

    load_dotenv()
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: set GROQ_API_KEY in your .env file "
              "(https://console.groq.com/keys)")
        sys.exit(1)

    pdf_paths = collect_pdf_paths(sys.argv[1:])
    if not pdf_paths:
        print("No PDFs found.")
        sys.exit(1)

    # reasoning_effort="low": gpt-oss is a reasoning model; under our forced
    #   tool_choice it otherwise spends its whole output budget "reasoning" and
    #   emits no tool call (Groq 400s). Low reasoning leaves room for the call.
    # max_tokens is set PER BINDING in src/agent.py (small for search, larger
    #   for the one submit), not here, to respect the free-tier token limit.
    # max_retries: on the free tier you can briefly exceed 8000 tokens/minute;
    #   the Groq client honors Retry-After and backs off instead of crashing.
    llm = ChatGroq(model=GROQ_MODEL, temperature=0,
                   reasoning_effort="low", max_retries=5)
    submit_llm = ChatGroq(model=SUBMIT_MODEL, temperature=0,
                          reasoning_effort="low", max_retries=5)

    # --- EXTRACT: one agent run per document. Each PDF is isolated: a failure
    # on one (a model JSON glitch, a hard rate limit) is reported and skipped so
    # the rest of the batch still produces a draft. An empty extraction (no
    # facts) is treated as a failure too.
    records = []
    for path in pdf_paths:
        source_name = os.path.basename(path)
        print(f"Reading {source_name} ...")
        doc_text = read_pdf(path)
        print(f"  extracting with {GROQ_MODEL} ...")
        try:
            record, final = extract_record(llm, doc_text, source_name,
                                            submit_llm=submit_llm)
            if not record.facts:
                print(f"  SKIPPED {source_name}: no facts extracted")
                continue
            print(f"  done: verified={final.get('verified')}  "
                  f"attempts={final.get('attempts')}")
            records.append(record)
        except Exception as e:
            print(f"  SKIPPED {source_name}: extraction failed ({e})")

    if not records:
        print("No documents could be extracted.")
        sys.exit(1)

    # GROUP: RECONCILE WITHIN GROUP
    checklist = json.load(open("data/nepqa_checklist.json"))
    groups = group_records(records)
    draft = build_multi_draft(records, checklist)

    os.makedirs("output", exist_ok=True)
    with open("output/draft.md", "w") as f:
        f.write(draft)

    print(f"\nGrouped {len(records)} source(s) into {len(groups)} product "
          "group(s).")
    print("Draft written to output/draft.md")


if __name__ == "__main__":
    main()
