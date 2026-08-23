"""Data models and schemas for the Aster & Row AI Support Agent."""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    title: str
    status: Literal["active", "superseded", "draft", "archived"] = "active"
    effective_date: Optional[str] = None
    superseded_date: Optional[str] = None
    last_reviewed: Optional[str] = None
    audience: Literal["customer", "internal"] = "customer"
    policy_authority: Literal["official", "none", "draft"] = "official"
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    customer_answering: bool = True
    filename: str


class DocumentChunk(BaseModel):
    chunk_id: str
    filename: str
    heading: str
    subheading: Optional[str] = None
    content: str
    metadata: DocumentMetadata
    score: float = 0.0


class Citation(BaseModel):
    filename: str
    heading: str
    document_id: Optional[str] = None

    def format_citation(self) -> str:
        return f"[{self.filename} > {self.heading}]"


class OrderItem(BaseModel):
    sku: Optional[str] = None
    name: str
    quantity: int
    final_sale: bool = False


class SafeOrderSummary(BaseModel):
    order_id: str
    membership_tier: Optional[str] = "standard"
    items: List[OrderItem] = Field(default_factory=list)
    placed_at: Optional[str] = None
    status: str
    status_updated_at: Optional[str] = None
    shipped_at: Optional[str] = None
    delivered_at: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[str] = None
    customer_safe_message: Optional[str] = None
    cancellation_eligible: Optional[bool] = None
    cancellation_window_notes: Optional[str] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    citations: Optional[List[Citation]] = None
    tool_calls: Optional[List[ToolCall]] = None
    handoff_recommended: Optional[bool] = None


class AgentResponse(BaseModel):
    content: str
    citations: List[Citation] = Field(default_factory=list)
    handoff_recommended: bool = False
    tool_calls: List[ToolCall] = Field(default_factory=list)
    conflicts_detected: List[str] = Field(default_factory=list)
    trace_id: Optional[str] = None


class ConversationTrace(BaseModel):
    trace_id: str
    session_id: str
    user_message: str
    conversation_history: List[Dict[str, Any]]
    retrieved_passages: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    final_response: str
    citations: List[Dict[str, Any]]
    handoff_recommended: bool
    conflicts_detected: List[str]
    notes: List[str] = Field(default_factory=list)
