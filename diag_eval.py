"""Diagnose eval failures in detail."""
import sys
sys.path.insert(0, '.')
from pathlib import Path
from evaluation.runner import check_case
from src.agent.orchestrator import AgentOrchestrator
from src.agent.llm import LLMClient
import json

orch = AgentOrchestrator(llm_client=LLMClient(provider='mock'))
vis = Path('evaluation/visible-cases.json')
ext = Path('evaluation/extended-cases.json')

all_cases = []
with open(vis) as f:
    for c in json.load(f)['cases']:
        c['suite'] = 'visible'
        all_cases.append(c)
with open(ext) as f:
    for c in json.load(f)['cases']:
        c['suite'] = 'extended'
        all_cases.append(c)

for case in all_cases:
    passed, failures = check_case(orch, case)
    status = 'PASS' if passed else 'FAIL'
    print(f"[{status}] {case['id']} ({case['category']})")
    for f in failures:
        print(f"       -> {f}")
