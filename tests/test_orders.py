"""Unit tests for Order Lookup Tool and privacy redactions."""
from src.tools.order_lookup import OrderLookupTool, normalize_order_id


def test_order_id_normalization():
    assert normalize_order_id("ord-1007") == "ORD-1007"
    assert normalize_order_id("  ORD_1007.  ") == "ORD-1007"
    assert normalize_order_id("ord 1007") == "ORD-1007"
    assert normalize_order_id("ORD1007") == "ORD-1007"


def test_order_lookup_privacy():
    tool = OrderLookupTool()
    res = tool.lookup("ORD-1007")
    assert res["success"] is True
    assert res["order_id"] == "ORD-1007"
    assert res["status"] == "shipped"
    
    # Assert private fields are completely redacted / absent
    assert "email" not in res
    assert "shipping_address" not in res
    assert "risk_score" not in res
    assert "warehouse_note" not in res
    assert "customer" not in res
    assert "internal" not in res


def test_cancelled_order_stale_eta_suppression():
    tool = OrderLookupTool()
    res = tool.lookup("ORD-1004")
    assert res["status"] == "cancelled"
    # Stale estimated delivery and carrier must be suppressed
    assert res["carrier"] is None
    assert res["estimated_delivery"] is None
    assert "cancelled" in res["customer_safe_message"]


def test_unknown_order():
    tool = OrderLookupTool()
    res = tool.lookup("ORD-9999")
    assert res["success"] is False
    assert res["error"] == "order_not_found"
    assert res["handoff_recommended"] is True
