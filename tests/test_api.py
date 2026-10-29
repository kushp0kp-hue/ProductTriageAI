import os
import tempfile
import unittest
from pathlib import Path
from app import create_app

VALID_PAYLOAD = {
    "title": "Portfolio balances update slowly",
    "description": "Customers report that portfolio balances remain stale for 8 to 12 seconds after a trade even though the order itself completes.",
    "customer_impact": "Major degradation",
    "frequency": "Often",
    "platform": "Web",
    "source": "Customer report",
}


class ProductTriageApiTests(unittest.TestCase):
    def setUp(self):
        self.old_key = os.environ.pop("OPENAI_API_KEY", None)
        self.temp_dir = tempfile.TemporaryDirectory()
        database = Path(self.temp_dir.name) / "test.db"
        self.app = create_app({"TESTING": True, "DATABASE": str(database)})
        self.client = self.app.test_client()

    def tearDown(self):
        if self.old_key is not None:
            os.environ["OPENAI_API_KEY"] = self.old_key
        self.temp_dir.cleanup()

    def test_health_reports_demo_mode_without_key(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["ai_mode"], "demo")

    def test_triage_creates_structured_result(self):
        response = self.client.post("/api/triage", json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 201)
        result = response.get_json()
        self.assertIn(result["priority"], {"P0", "P1", "P2", "P3"})
        self.assertTrue(result["labels"])
        self.assertTrue(result["acceptance_criteria"])
        self.assertEqual(result["mode"], "demo")

    def test_short_description_returns_400(self):
        payload = dict(VALID_PAYLOAD)
        payload["description"] = "Too short"
        response = self.client.post("/api/triage", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_history_returns_saved_triage(self):
        self.client.post("/api/triage", json=VALID_PAYLOAD)
        response = self.client.get("/api/triage?limit=5")
        items = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], VALID_PAYLOAD["title"])

    def test_history_limit_validation(self):
        response = self.client.get("/api/triage?limit=abc")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
