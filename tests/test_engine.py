import os
import unittest
from app.ai_engine import ProductTriageEngine


class DemoEngineTests(unittest.TestCase):
    def setUp(self):
        self.old_key = os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self):
        if self.old_key is not None:
            os.environ["OPENAI_API_KEY"] = self.old_key

    def test_security_issue_escalates(self):
        engine = ProductTriageEngine()
        result = engine.analyze({
            "title": "Unauthorized account access",
            "description": "A customer reports possible unauthorized access and exposed account data.",
            "customer_impact": "Blocks core task",
            "frequency": "Sometimes",
            "platform": "Web",
            "source": "Customer report",
        })
        self.assertEqual(result["priority"], "P0")
        self.assertEqual(result["owner_team"], "Security")

    def test_financial_issue_is_high_priority(self):
        engine = ProductTriageEngine()
        result = engine.analyze({
            "title": "Portfolio balance refresh is delayed",
            "description": "Customers see stale balances for 10 seconds after a successful trade.",
            "customer_impact": "Major degradation",
            "frequency": "Often",
            "platform": "Web",
            "source": "Customer report",
        })
        self.assertEqual(result["priority"], "P1")
        self.assertEqual(result["category"], "Financial Experience")

    def test_result_has_required_structure(self):
        engine = ProductTriageEngine()
        result = engine.analyze({
            "title": "Search page is slow",
            "description": "The search page takes 4 seconds to return results during peak usage.",
            "customer_impact": "Minor inconvenience",
            "frequency": "Sometimes",
            "platform": "Web",
            "source": "Product analytics",
        })
        required = {
            "priority", "category", "owner_team", "impact_level", "confidence",
            "summary", "rationale", "next_action", "labels", "acceptance_criteria",
            "follow_up_questions",
        }
        self.assertEqual(set(result.keys()), required)


if __name__ == "__main__":
    unittest.main()
