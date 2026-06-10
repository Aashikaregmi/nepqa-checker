"""Reconciliation stage: combine DocRecords into a compliance decision."""

from .schema import DocRecord


def reconcile(records: list[DocRecord]) -> dict:
    """Reconcile extracted records against the NEPQA checklist.

    Will cross-check facts across documents, apply the checklist rules in
    data/nepqa_checklist.json, and produce a decision describing which
    requirements pass, fail, or are missing.

    Not implemented yet.
    """
    raise NotImplementedError
