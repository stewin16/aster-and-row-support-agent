"""Unittest test suite discovering all test cases."""
import unittest
from pathlib import Path
from evaluation.runner import check_case
from src.agent.orchestrator import AgentOrchestrator
from src.config import EVALUATION_DIR
import json


from src.agent.llm import LLMClient


class TestEvaluationSuites(unittest.TestCase):
    """Runs all visible and extended evaluation cases via unittest."""

    @classmethod
    def setUpClass(cls):
        cls.orchestrator = AgentOrchestrator(llm_client=LLMClient(provider="mock"))
        cls.visible_cases = []
        cls.extended_cases = []

        vis_path = EVALUATION_DIR / "visible-cases.json"
        if vis_path.exists():
            with open(vis_path, "r", encoding="utf-8") as f:
                cls.visible_cases = json.load(f).get("cases", [])

        ext_path = EVALUATION_DIR / "extended-cases.json"
        if ext_path.exists():
            with open(ext_path, "r", encoding="utf-8") as f:
                cls.extended_cases = json.load(f).get("cases", [])

    def test_visible_cases(self):
        for case in self.visible_cases:
            with self.subTest(case_id=case["id"]):
                passed, failures = check_case(self.orchestrator, case)
                self.assertTrue(passed, f"Case {case['id']} failed: {failures}")

    def test_extended_cases(self):
        for case in self.extended_cases:
            with self.subTest(case_id=case["id"]):
                passed, failures = check_case(self.orchestrator, case)
                self.assertTrue(passed, f"Extended case {case['id']} failed: {failures}")


if __name__ == "__main__":
    unittest.main()
