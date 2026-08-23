"""Main Agent Orchestrator coordinating sessions, tools, RAG, and guardrails."""
import re
import uuid
from typing import Dict, List, Any, Optional
from src.models import AgentResponse, Citation, ToolCall, Message
from src.rag.retriever import KnowledgeRetriever
from src.tools.order_lookup import OrderLookupTool, extract_order_id, normalize_order_id
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.llm import LLMClient
from src.agent.observability import AgentTracer


class AgentOrchestrator:
    """Coordinates multi-turn conversations, RAG retrieval, tool execution, and guardrails."""

    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        order_tool: Optional[OrderLookupTool] = None,
        llm_client: Optional[LLMClient] = None,
        tracer: Optional[AgentTracer] = None
    ):
        self.retriever = retriever or KnowledgeRetriever()
        self.order_tool = order_tool or OrderLookupTool()
        self.llm_client = llm_client or LLMClient()
        self.tracer = tracer or AgentTracer()
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Returns valid session_id."""
        if not session_id:
            session_id = f"session-{uuid.uuid4().hex[:8]}"
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return session_id

    def reset_session(self, session_id: str):
        """Clears a conversation session."""
        if session_id in self.sessions:
            self.sessions[session_id] = []

    def chat(self, user_message: str, session_id: Optional[str] = None) -> AgentResponse:
        """Processes a single conversational turn."""
        sid = self.get_or_create_session(session_id)
        history = self.sessions[sid]
        msg_lower = user_message.lower()

        # Step 1: Detect Order Queries and Extract Order ID
        order_id = extract_order_id(user_message)
        # If not in current message, look back in recent session messages if user asks a follow-up about the order
        if not order_id and ("order" in msg_lower or "arrive" in msg_lower or "ship" in msg_lower or "status" in msg_lower):
            for prev in reversed(history):
                prev_id = extract_order_id(prev.get("content", ""))
                if prev_id:
                    order_id = prev_id
                    break

        tool_calls: List[ToolCall] = []
        order_data: Optional[Dict[str, Any]] = None
        handoff_recommended = False
        notes: List[str] = []

        # Check for order intent
        is_order_query = bool(order_id) or any(
            phrase in msg_lower for phrase in [
                "where is my order", "order status", "track my order", "check order",
                "when will order", "when will ord-", "check ord-"
            ]
        )

        if is_order_query:
            if order_id:
                # Perform sanitized lookup
                lookup_result = self.order_tool.lookup(order_id)
                tool_calls.append(
                    ToolCall(
                        name="order_lookup",
                        arguments={"order_id": order_id},
                        result=lookup_result
                    )
                )
                order_data = lookup_result
                if lookup_result.get("handoff_recommended"):
                    handoff_recommended = True
            else:
                # Missing order ID - tool cannot be called without ID
                notes.append("Order query without order ID. Requesting order ID from user.")

        # Step 2: RAG Passage Retrieval
        # Construct search query (combining last user turn for multi-turn context if needed)
        search_query = user_message
        if history and len(user_message.split()) <= 6:
            prev_user_msgs = [m["content"] for m in history if m["role"] == "user"]
            if prev_user_msgs:
                search_query = f"{prev_user_msgs[-1]} {user_message}"

        retrieved_chunks, conflicts = self.retriever.retrieve(
            query=search_query,
            top_k=4,
            include_internal=("migration" in msg_lower or "scratchpad" in msg_lower)
        )

        # Step 3: Determine Handoff Recommendation
        # Handoff cases:
        # - Document conflicts detected
        # - Damaged item on final sale requiring human review
        # - Insufficient information (e.g. vegan materials)
        # - Order not found or order status == exception
        # - User requesting internal data or action completion
        if conflicts:
            handoff_recommended = True
            notes.append("Active document conflict detected.")

        if "vegan" in msg_lower or "cruelty free" in msg_lower:
            handoff_recommended = True
            notes.append("Knowledge base information insufficient.")

        if "damage" in msg_lower or "broken" in msg_lower or "defective" in msg_lower:
            if "final" in msg_lower or "sale" in msg_lower:
                handoff_recommended = True
                notes.append("Damaged item claim requires human review.")

        if "risk score" in msg_lower or "internal note" in msg_lower or ("email" in msg_lower and "address" in msg_lower and "ord-" in msg_lower):
            handoff_recommended = True
            notes.append("Privacy policy enforcement - internal data request.")

        if "gift card" in msg_lower and any(num in msg_lower for num in ["ar-gift", "code", "balance"]):
            handoff_recommended = True
            notes.append("Gift card security - human specialist handoff.")

        if "cancel" in msg_lower and order_data and order_data.get("status") in ("processing", "shipped", "delivered"):
            handoff_recommended = True
            notes.append("Cancellation request on processing/shipped order requires specialist.")

        if order_data and not order_data.get("success") and order_data.get("error") == "order_not_found":
            handoff_recommended = True
            notes.append("Order ID not found.")

        # Step 4: Generate Response via LLM Adapter
        response_text = self.llm_client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            history=history,
            retrieved_chunks=retrieved_chunks,
            order_data=order_data,
            conflicts=conflicts,
            handoff_recommended=handoff_recommended
        )

        # Step 5: Extract and Filter Citations
        citations: List[Citation] = []
        # Check citations from response or retrieved chunks
        if not is_order_query and not ("risk score" in msg_lower or "internal note" in msg_lower):
            # Parse citations from response (supports both [file.md > heading] and 【file.md > heading】)
            citation_pattern = re.findall(r"[\[【]([0-9a-zA-Z\-_]+\.md)\s*[>›]\s*([^\]】]+)[\]】]", response_text)
            seen = set()
            for fn, hd in citation_pattern:
                # Do not allow superseded or draft files as citations
                if fn not in ("02-returns-policy-legacy.md", "14-internal-content-migration-notes.md"):
                    clean_hd = hd.strip().strip("'\"#.,:;")
                    if (fn, clean_hd) not in seen:
                        seen.add((fn, clean_hd))
                        citations.append(Citation(filename=fn, heading=clean_hd))

            # If no inline citations were generated but chunks were retrieved and used
            if not citations and retrieved_chunks and "insufficient" not in response_text.lower():
                for c in retrieved_chunks:
                    if c.metadata.customer_answering and c.metadata.status == "active":
                        key = (c.filename, c.heading)
                        if key not in seen:
                            seen.add(key)
                            citations.append(Citation(filename=c.filename, heading=c.heading))
                        if len(citations) >= 2:
                            break

        # Step 6: Create Structured Trace
        trace = self.tracer.create_trace(
            session_id=sid,
            user_message=user_message,
            conversation_history=history,
            retrieved_passages=[c.model_dump() for c in retrieved_chunks],
            tool_calls=[tc.model_dump() for tc in tool_calls],
            final_response=response_text,
            citations=citations,
            handoff_recommended=handoff_recommended,
            conflicts_detected=conflicts,
            notes=notes
        )

        # Step 7: Update Session History
        self.sessions[sid].append({"role": "user", "content": user_message})
        self.sessions[sid].append({"role": "assistant", "content": response_text})

        return AgentResponse(
            content=response_text,
            citations=citations,
            handoff_recommended=handoff_recommended,
            tool_calls=tool_calls,
            conflicts_detected=conflicts,
            trace_id=trace.trace_id
        )
