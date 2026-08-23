"""FastAPI Backend Server providing REST API and static UI serving."""
from pathlib import Path
import sys

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.agent.orchestrator import AgentOrchestrator
from src.agent.llm import LLMClient
from src.config import BASE_DIR, EVALUATION_DIR
from evaluation.runner import check_case, run_evaluation_suite
import json

app = FastAPI(
    title="Aster & Row AI Support Agent API",
    description="RAG and tool-calling support agent backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Live chat orchestrator (powered by Groq / LLM provider)
orchestrator = AgentOrchestrator()
# Deterministic evaluation orchestrator (runs instantly without rate limits)
eval_orchestrator = AgentOrchestrator(llm_client=LLMClient(provider="mock"))

WEB_DIR = BASE_DIR / "web"


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ResetRequest(BaseModel):
    session_id: str


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Processes a user message through the support agent."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    response = orchestrator.chat(
        user_message=request.message,
        session_id=request.session_id
    )
    return {
        "content": response.content,
        "citations": [c.model_dump() for c in response.citations],
        "handoff_recommended": response.handoff_recommended,
        "tool_calls": [tc.model_dump() for tc in response.tool_calls],
        "conflicts_detected": response.conflicts_detected,
        "trace_id": response.trace_id
    }


@app.post("/api/reset")
async def reset_endpoint(request: ResetRequest):
    """Resets conversation session history."""
    orchestrator.reset_session(request.session_id)
    return {"status": "ok", "session_id": request.session_id}


@app.get("/api/trace/{trace_id}")
async def get_trace_endpoint(trace_id: str):
    """Retrieves structured trace for observability."""
    trace = orchestrator.tracer.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace.model_dump()


@app.get("/api/evaluation/run")
async def run_eval_endpoint():
    """Runs the visible and extended evaluation suites and returns JSON results."""
    vis_file = EVALUATION_DIR / "visible-cases.json"
    ext_file = EVALUATION_DIR / "extended-cases.json"

    all_cases = []
    if vis_file.exists():
        with open(vis_file, "r", encoding="utf-8") as f:
            for c in json.load(f).get("cases", []):
                c["suite"] = "visible"
                all_cases.append(c)

    if ext_file.exists():
        with open(ext_file, "r", encoding="utf-8") as f:
            for c in json.load(f).get("cases", []):
                c["suite"] = "extended"
                all_cases.append(c)

    case_results = []
    category_breakdown: Dict[str, Dict[str, int]] = {}
    passed_count = 0

    for case in all_cases:
        passed, failures = check_case(eval_orchestrator, case)
        cat = case.get("category", "general")
        if cat not in category_breakdown:
            category_breakdown[cat] = {"passed": 0, "total": 0}
        category_breakdown[cat]["total"] += 1
        if passed:
            passed_count += 1
            category_breakdown[cat]["passed"] += 1

        case_results.append({
            "id": case.get("id"),
            "suite": case.get("suite"),
            "category": cat,
            "passed": passed,
            "failures": failures
        })

    return {
        "total_cases": len(all_cases),
        "passed_cases": passed_count,
        "overall_accuracy": round((passed_count / len(all_cases)) * 100.0, 1) if all_cases else 0.0,
        "category_breakdown": category_breakdown,
        "cases": case_results
    }


# Mount static web directory
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(WEB_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
