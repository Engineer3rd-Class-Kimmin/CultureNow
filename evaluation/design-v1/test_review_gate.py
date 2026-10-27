"""Negative controls: unresolved reviews must never be reported as a complete pass."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("design_review", HERE / "run.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewGateTests(unittest.TestCase):
    def test_original_six_unresolved_scenarios_fail(self):
        cases = json.loads((HERE / "baseline/cases.json").read_text(encoding="utf-8"))
        rows = review.evaluate_cases(cases, HERE.parents[1])
        self.assertEqual(sum(c["status"] == "FAIL" for c in rows), 6)

    def test_partial_and_gap_fail_even_with_present_evidence(self):
        cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        for verdict in ("PARTIAL", "GAP", "UNKNOWN"):
            with self.subTest(verdict=verdict):
                changed = {**cases[0], "verdict": verdict}
                row = review.evaluate_cases([changed], HERE.parents[1])[0]
                self.assertTrue(row["evidence_found"])
                self.assertEqual(row["status"], "FAIL")

    def test_missing_quote_fails_despite_supported_verdict(self):
        case = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))[0]
        row = review.evaluate_cases([{**case, "evidence_quote": "missing-evidence-marker"}], HERE.parents[1])[0]
        self.assertEqual(row["status"], "FAIL")

    def test_empty_quote_does_not_pass(self):
        case = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))[0]
        row = review.evaluate_cases([{**case, "evidence_quote": ""}], HERE.parents[1])[0]
        self.assertEqual(row["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
