# NEPQA Inverter Import-Paperwork Checker

A tool I built to help SunBridge Trading prepare its inverter paperwork for a
Nepal import review. It reads the manufacturer PDFs, compares them, and writes
a draft the import agent can review, checked against the NEPQA-2025 §1.4
guideline for grid-connected inverters.

To be clear up front: this is **not** a quality test of the product — that
testing is done by RETS in Nepal. This tool only checks whether the *paperwork*
is complete and consistent, and flags what is missing or needs to be asked from
the factory.

## What I found in the two PDFs

The two PDFs are not the same product. They share a factory (NingBo Deye), but
one is a Deye three-phase string inverter (SUN series) and the other a CHISAGE
single-phase microinverter (CE series) — no model number appears in both, so
they can't be compared side by side.

Neither is complete on its own against NEPQA §1.4: Deye has the grid
certificates (IEC 61727, 62116) but not the safety or MPPT ones; CHISAGE has
only the safety one (IEC 62109-1). The draft says this honestly rather than
forcing the two into one filing — so its first point is that they differ.

## How it works (the LLM only reads; my code judges)

The language model is only allowed to *read* the documents and pull out facts.
It never decides pass or fail — all judging is plain Python. If the model did
the deciding, it could quietly smooth over a disagreement; my code can't.

Three stages:

- **Extract** — reads each PDF's text and asks the model to fill a fixed shape
  where every fact carries the exact quote it came from. Anything not stated is
  left empty, never guessed. The only place the model is used.
- **Reconcile** — pure Python. Checks whether the two records are even the same
  product (shared model, same phase); if not, marks them not comparable instead
  of inventing conflicts.
- **Score & generate** — pure Python. Scores each record against the checklist
  and writes the draft.
- **Streamlit UI** — `app.py` is a thin web wrapper around the same functions;
  it adds no new logic.

Every fact keeps its source and quote because the Pydantic schema requires it —
that's what keeps the pipeline honest end to end.

## Repo structure

```
src/
  schema.py       Pydantic models: Fact (value + source + quote), DocRecord
  extract.py      stage 1 — PDF -> DocRecord (the only LLM step)
  reconcile.py    stage 2 — two DocRecords -> same/different + fact comparison
  generate.py     stage 3 — score vs checklist -> Markdown draft
data/
  nepqa_checklist.json   NEPQA §1.4 requirements, hand-encoded
sources/          input PDFs (gitignored)
output/           extracted records + draft.md
tests/            reconcile tests
run_extract.py    PDF        -> output/<name>_record.json
run_reconcile.py  two records -> reconcile result (debug)
run_generate.py   records    -> output/draft.md
```

## How to run it

```
pip install -r requirements.txt

# put your key in a .env file:
#   GEMINI_API_KEY=...

python3 run_extract.py sources/<file>.pdf   # one PDF -> output/<name>_record.json
python3 run_generate.py                      # builds output/draft.md
python3 -m pytest tests/                      # runs the reconcile tests

streamlit run app.py                          # web UI
```

The extracted records are committed, so `run_generate.py` and the tests work
without any API calls.

The web UI lets you upload PDFs, run the pipeline (live or using saved
records), view the draft, and download it as `.md` or `.pdf`.

## Things I deliberately left out

- **No database** — files in, file out. Nothing to store between runs.
- **No orchestration library** (LangGraph etc.) — the pipeline is a straight
  three-step line. A verifier step is where one would actually fit later.
- **No FastAPI** — this is one self-contained tool, not a service.

## What could be better

- Standard matching keys on the IEC number in the text (e.g. `62109-1`) and
  assumes a normal wording; an unusual phrasing could slip past it.
- The NEPQA checklist in `data/` is hand-encoded from §1.4, so it must be
  updated by hand if NEPQA changes.
- A free-tier model reads the PDFs, so the extracted records are committed to
  let the later stages run without API calls.
- The PDF export strips markdown formatting bluntly (removes `#`, `*`, and
  dash-only lines), so it is plain text, not styled.
- The UI has a checkbox to reuse saved records so testing does not spend API
  quota.
