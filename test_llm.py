"""Quick smoke test for the LLM pipeline — run to verify Groq RAG path works."""
import sys, os
sys.path.insert(0, '.')

from src.agent.llm import LLMClient
from src.rag.retriever import KnowledgeRetriever

client = LLMClient(provider='groq')
retriever = KnowledgeRetriever()

query = "How long do I have to return a backpack?"
chunks, conflicts = retriever.retrieve(query, top_k=4)

print(f"Retrieved {len(chunks)} chunks, {len(conflicts)} conflicts")
for c in chunks:
    print(f"  [{c.filename} > {c.heading}] score={c.score}")

from src.agent.prompts import SYSTEM_PROMPT
result = client.generate(
    system_prompt=SYSTEM_PROMPT,
    user_message=query,
    history=[],
    retrieved_chunks=chunks,
    order_data=None,
    conflicts=conflicts,
    handoff_recommended=False
)
print("\n=== RESPONSE ===")
print(result)
