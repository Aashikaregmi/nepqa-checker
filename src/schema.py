"""
schema.py — the data shapes for the whole pipeline (PR1).

Two Pydantic models:
  - Fact: one extracted value, always carrying its source + supporting quote.
  - DocRecord: everything extracted from ONE document, with identity fields
    pulled out so reconcile (PR3) can detect same-product vs different-product.

The LLM (PR2) must return data in these shapes. If a value isn't stated in
the document, it is None — never guessed.
"""
from pydantic import BaseModel, Field


class Fact(BaseModel):
    """One extracted piece of information, with provenance attached."""
    value: str | None = Field(
        default=None,
        description=(
            "The extracted value, or None if the document does not "
            "state it."
        ),
    )
    source: str = Field(
        description="Which document this came from (e.g. the file name).",
    )
    quote: str | None = Field(
        default=None,
        description=(
            "Exact supporting text from the document. None if value "
            "is None."
        ),
    )


class DocRecord(BaseModel):
    """Everything extracted from a single document."""

    # --- Identity fields: used by reconcile to tell same vs different ---
    doc_type: str | None = Field(
        default=None,
        description=(
            "What kind of document this is (e.g. 'safety test "
            "report', 'grid-interface certificate'). Read off the "
            "document, not inferred."
        ),
    )
    model_series: str | None = Field(
        default=None,
        description=(
            "Model name(s) or series the document describes."
        ),
    )
    phase: str | None = Field(
        default=None,
        description="'single' or 'three' phase, if stated.",
    )
    voltage_class: str | None = Field(
        default=None,
        description=(
            "Rough DC input voltage class (e.g. '60V', '1100V'), "
            "if stated."
        ),
    )

    # --- All other extracted facts, keyed by field name ---
    facts: dict[str, Fact] = Field(
        default_factory=dict,
        description=(
            "Other extracted facts (ratings, standards, label "
            "fields), each a Fact with its own source and quote."
        ),
    )
