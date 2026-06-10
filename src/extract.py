"""
Read one PDF and return a DocRecord (PR2).

The only stage that uses the LLM. It reads the PDF text with pdfplumber,
then asks the model to fill in the DocRecord shape, attaching a quote to
every fact and using None when something isn't stated.
"""
import os

import instructor
import pdfplumber
from google import genai
from dotenv import load_dotenv

from .schema import DocRecord

load_dotenv()

client = instructor.from_genai(
    genai.Client(api_key=os.environ["GEMINI_API_KEY"])
)


def read_pdf_text(pdf_path: str, max_pages: int | None = None) -> str:
    """Open a PDF and return its text. Optionally cap the number of pages."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
        for page in pages:
            text += (page.extract_text() or "") + "\n"
    return text


def extract(pdf_path: str) -> DocRecord:
    """Read a PDF and return a DocRecord with identity fields filled in."""
    source_name = os.path.basename(pdf_path)
    document_text = read_pdf_text(pdf_path, max_pages=12)

    prompt = (
        "You are reading one compliance document for a solar PV inverter.\n"
        "Fill in the requested fields from the text below.\n"
        "Rules:\n"
        "- Use only what the document actually states.\n"
        "- If a field is not stated, leave it as null. Never guess.\n"
        "- doc_type: what kind of document this is, in a few words "
        "(read it off the document, do not infer).\n"
        "- model_series: the model name(s) or series described.\n"
        "- phase: 'single' or 'three' if stated.\n"
        "- voltage_class: rough max DC input voltage "
        "(e.g. '60V', '1100V') if stated.\n"
        "- Also return a 'facts' list. Add one entry for each of these "
        "that the document states (skip ones not stated):\n"
        "    standards, ip_rating, output_frequency, ac_output_voltage,\n"
        "    power_factor, rated_power, warranty.\n"
        "- Each fact entry has: field_name (one of the names above), "
        "value, source, and quote (exact text from the document).\n"
        "- Example fact entry:\n"
        '    {"field_name": "ip_rating", "value": "IP65", '
        '"source": "doc.pdf", "quote": "Protection degree IP65"}\n'
        f"- For every field, set source to '{source_name}'.\n\n"
        f"DOCUMENT TEXT:\n{document_text}"
    )

    record = client.messages.create(
        model="gemini-2.5-flash-lite",
        messages=[{"role": "user", "content": prompt}],
        response_model=DocRecord,
    )
    return record
