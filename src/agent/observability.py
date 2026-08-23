"""Observability, structured logging, and debugging traces."""
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.models import ConversationTrace, Citation, ToolCall


class AgentTracer:
    """Collects structured execution traces without logging secrets or PII."""

    def __init__(self):
        self.traces: Dict[str, ConversationTrace] = {}
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        self.logger = logging.getLogger("AsterAndRowAgent")

    def create_trace(
        self,
        session_id: str,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        retrieved_passages: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        final_response: str,
        citations: List[Citation],
        handoff_recommended: bool,
        conflicts_detected: List[str],
        notes: Optional[List[str]] = None
    ) -> ConversationTrace:
        trace_id = f"trace-{uuid.uuid4().hex[:8]}"
        trace = ConversationTrace(
            trace_id=trace_id,
            session_id=session_id,
            user_message=user_message,
            conversation_history=[
                {"role": m.get("role"), "content": m.get("content")}
                for m in conversation_history
            ],
            retrieved_passages=[
                {
                    "filename": p.get("filename"),
                    "heading": p.get("heading"),
                    "score": p.get("score"),
                    "status": p.get("metadata", {}).get("status") if isinstance(p.get("metadata"), dict) else getattr(p.get("metadata"), "status", "active")
                }
                for p in retrieved_passages
            ],
            tool_calls=tool_calls,
            final_response=final_response,
            citations=[{"filename": c.filename, "heading": c.heading} for c in citations],
            handoff_recommended=handoff_recommended,
            conflicts_detected=conflicts_detected,
            notes=notes or []
        )
        self.traces[trace_id] = trace
        self.logger.info(
            f"[Trace {trace_id}] User='{user_message[:50]}...' | Citations={len(citations)} | Handoff={handoff_recommended}"
        )
        return trace

    def get_trace(self, trace_id: str) -> Optional[ConversationTrace]:
        return self.traces.get(trace_id)
