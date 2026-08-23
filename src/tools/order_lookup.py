"""Order lookup tool with strict privacy redaction, input normalization, and status precedence."""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import ORDERS_FILE, DEFAULT_SNAPSHOT_TIME
from src.models import SafeOrderSummary, OrderItem


def normalize_order_id(raw_id: str) -> str:
    """Normalizes order ID (e.g., ' ord-1007. ' -> 'ORD-1007')."""
    if not raw_id:
        return ""
    # Strip whitespace, quotes, and punctuation around ID
    cleaned = raw_id.strip().strip("'\"#.,:;").upper()
    # Match standard pattern ORD-XXXX
    match = re.search(r"ORD[-_\s]?\d+", cleaned, re.IGNORECASE)
    if match:
        matched_str = match.group(0).upper().replace("_", "-").replace(" ", "-")
        if "-" not in matched_str:
            matched_str = matched_str[:3] + "-" + matched_str[3:]
        return matched_str
    return cleaned


def extract_order_id(text: str) -> Optional[str]:
    """Extracts an order ID from text if present."""
    match = re.search(r"\bORD[-_\s]?\d+\b", text, re.IGNORECASE)
    if match:
        return normalize_order_id(match.group(0))
    return None


class OrderLookupTool:
    """Secure, privacy-preserving order lookup tool."""

    def __init__(self, orders_file: Path = ORDERS_FILE):
        self.orders_file = orders_file
        self.orders_by_id: Dict[str, Dict[str, Any]] = {}
        self.snapshot_at = DEFAULT_SNAPSHOT_TIME
        self._load_orders()

    def _load_orders(self):
        """Loads orders dataset from disk."""
        if not self.orders_file.exists():
            return
        with open(self.orders_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.snapshot_at = data.get("snapshot_at", DEFAULT_SNAPSHOT_TIME)
        for order in data.get("orders", []):
            order_id = normalize_order_id(order.get("order_id", ""))
            if order_id:
                self.orders_by_id[order_id] = order

    def lookup(self, order_id_input: str) -> Dict[str, Any]:
        """
        Looks up an order by ID, applying privacy redaction and status precedence rules.
        Returns a sanitized JSON dictionary.
        """
        normalized_id = normalize_order_id(order_id_input)
        if not normalized_id:
            return {
                "success": False,
                "error": "missing_order_id",
                "message": "Please provide an order ID (e.g., ORD-1007) to check your order status.",
                "handoff_recommended": False
            }

        raw_order = self.orders_by_id.get(normalized_id)
        if not raw_order:
            return {
                "success": False,
                "error": "order_not_found",
                "order_id": normalized_id,
                "message": f"Order {normalized_id} was not found in our records. Please check the order ID or contact customer support for assistance.",
                "handoff_recommended": True
            }

        status = raw_order.get("status", "unknown").lower()
        items_raw = raw_order.get("items", [])
        safe_items = [
            {
                "name": item.get("name", ""),
                "quantity": item.get("quantity", 1),
                "final_sale": bool(item.get("final_sale", False))
            }
            for item in items_raw
        ]

        # Calculate cancellation eligibility based on snapshot_at and placed_at
        cancellation_eligible = False
        cancellation_notes = None
        if status == "pending":
            try:
                placed_dt = datetime.fromisoformat(raw_order.get("placed_at", "").replace("Z", "+00:00"))
                snapshot_dt = datetime.fromisoformat(self.snapshot_at.replace("Z", "+00:00"))
                diff_minutes = (snapshot_dt - placed_dt).total_seconds() / 60.0
                if diff_minutes <= 30:
                    cancellation_eligible = True
                    cancellation_notes = f"Order was placed {int(diff_minutes)} minutes ago (within the 30-minute pending cancellation window)."
                else:
                    cancellation_notes = f"Order was placed {int(diff_minutes)} minutes ago (exceeded the 30-minute pending cancellation window)."
            except Exception:
                pass

        # Apply status precedence to suppress stale delivery fields on cancelled/returned orders
        is_cancelled = status == "cancelled"
        is_returned = status == "returned"
        is_exception = status == "exception"
        is_shipped = status == "shipped"

        carrier = raw_order.get("carrier")
        tracking_number = raw_order.get("tracking_number")
        estimated_delivery = raw_order.get("estimated_delivery")
        customer_safe_message = raw_order.get("customer_safe_message")

        if is_cancelled:
            carrier = None
            tracking_number = None
            estimated_delivery = None
            customer_safe_message = "The order was cancelled and will not be shipped."

        elif is_returned:
            carrier = None
            tracking_number = None
            estimated_delivery = None
            customer_safe_message = "The return was received and processed."

        elif is_shipped and not estimated_delivery:
            customer_safe_message = (
                f"The order has shipped with {carrier or 'the carrier'}. "
                f"A delivery estimate is not currently available."
            )

        handoff_recommended = is_exception

        # Construct sanitized payload (NO customer email, address, internal notes, risk scores)
        sanitized_summary = {
            "success": True,
            "order_id": normalized_id,
            "membership_tier": raw_order.get("membership_tier", "standard"),
            "status": status,
            "status_updated_at": raw_order.get("status_updated_at"),
            "placed_at": raw_order.get("placed_at"),
            "items": safe_items,
            "carrier": carrier,
            "tracking_number": tracking_number,
            "estimated_delivery": estimated_delivery,
            "customer_safe_message": customer_safe_message,
            "cancellation_eligible": cancellation_eligible,
            "cancellation_window_notes": cancellation_notes,
            "handoff_recommended": handoff_recommended
        }

        return sanitized_summary
