"""Tests for the deterministic reconcile logic (PR3)."""
from src.schema import DocRecord, Fact
from src.reconcile import reconcile, same_product


def _rec(models, phase, facts=None):
    return DocRecord(model_series=models, phase=phase, facts=facts or [])


def test_different_products_are_out_of_scope():
    """Different models + different phase -> DIFFERENT_PRODUCT, no rows."""
    a = _rec("SUN-5K-G06P3-EU-AM2", "three")
    b = _rec("CE-1P20001G-230-EU", "single")
    result = reconcile(a, b)
    assert result["verdict"] == "DIFFERENT_PRODUCT"
    assert result["rows"] == []


def test_same_product_confirms_matching_fact():
    """Same model + phase, agreeing fact -> CONFIRMED."""
    fa = [
        Fact(field_name="ip_rating", value="IP65",
             source="a.pdf", quote="IP65"),
    ]
    fb = [
        Fact(field_name="ip_rating", value="IP65",
             source="b.pdf", quote="IP65"),
    ]
    a = _rec("SUN-5K-G06P3-EU-AM2", "three", fa)
    b = _rec("SUN-5K-G06P3-EU-AM2", "three", fb)
    result = reconcile(a, b)
    assert result["verdict"] == "SAME_PRODUCT"
    assert result["rows"][0]["status"] == "CONFIRMED"


def test_same_product_flags_conflicting_fact():
    """Same product, disagreeing fact -> CONFLICT."""
    fa = [
        Fact(field_name="ip_rating", value="IP65",
             source="a.pdf", quote="IP65"),
    ]
    fb = [
        Fact(field_name="ip_rating", value="IP67",
             source="b.pdf", quote="IP67"),
    ]
    a = _rec("SUN-5K-G06P3-EU-AM2", "three", fa)
    b = _rec("SUN-5K-G06P3-EU-AM2", "three", fb)
    result = reconcile(a, b)
    assert result["rows"][0]["status"] == "CONFLICT"