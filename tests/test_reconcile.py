"""Tests for the deterministic reconcile logic (PR3)."""
from src.schema import DocRecord, Fact
from src.reconcile import reconcile


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
    assert result["verdict"] == "SAME_PRODUCT"


def test_whitespace_difference_is_not_a_conflict():
    """'50Hz' vs '50 Hz' should normalize to the same -> CONFIRMED."""
    fa = [
        Fact(field_name="output_frequency", value="50Hz",
             source="a.pdf", quote="50Hz"),
    ]
    fb = [
        Fact(field_name="output_frequency", value="50 Hz",
             source="b.pdf", quote="50 Hz"),
    ]
    a = _rec("SUN-5K-G06P3-EU-AM2", "three", fa)
    b = _rec("SUN-5K-G06P3-EU-AM2", "three", fb)
    result = reconcile(a, b)
    assert result["rows"][0]["status"] == "CONFIRMED"


def test_genuine_difference_still_conflicts_after_normalize():
    """A real value difference must still be flagged after normalizing."""
    fa = [
        Fact(field_name="output_frequency", value="50 Hz",
             source="a.pdf", quote="50 Hz"),
    ]
    fb = [
        Fact(field_name="output_frequency", value="60 Hz",
             source="b.pdf", quote="60 Hz"),
    ]
    a = _rec("SUN-5K-G06P3-EU-AM2", "three", fa)
    b = _rec("SUN-5K-G06P3-EU-AM2", "three", fb)
    result = reconcile(a, b)
    assert result["rows"][0]["status"] == "CONFLICT"
