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
    field_name: str = Field(
        description=(
            "What this fact is about, e.g. 'ip_rating', 'standards'."
        ),
    )
    value: str | None = Field(
        default=None,
        description="The extracted value, or None if not stated.",
    )
    source: str = Field(
        description="Which document this came from.",
    )
    quote: str | None = Field(
        default=None,
        description="Exact supporting text. None if value is None.",
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

    # --- All other extracted facts, as a flat list ---
    facts: list[Fact] = Field(
        default_factory=list,
        description=(
            "List of extracted facts, each with field_name, value, "
            "source, quote."
        ),
    )
