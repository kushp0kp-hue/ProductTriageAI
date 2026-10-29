import json
import os
import re

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

SYSTEM_INSTRUCTIONS = """
You are ProductTriageAI, an AI product-operations assistant.
Turn a raw product/software issue into a concise structured triage recommendation
that a Product Owner can review. Be practical rather than dramatic. Do not mark
everything critical. Use only supplied evidence; when information is missing, ask
a follow-up question instead of inventing facts.

Return valid JSON only with EXACTLY these keys:
priority, category, owner_team, impact_level, confidence, summary, rationale,
next_action, labels, acceptance_criteria, follow_up_questions

Rules:
- priority: P0, P1, P2, or P3
- impact_level: Critical, High, Medium, or Low
- confidence: integer 0-100
- labels: 2-5 short lowercase strings
- acceptance_criteria: 2-5 concise strings
- follow_up_questions: 0-4 concise strings
- owner_team: plausible functional owner such as Backend, Frontend, Platform,
  Product, Data, Security, Support, or Mobile
- category: concise product/engineering category
- summary: maximum 2 sentences
- rationale: maximum 3 sentences
- next_action: one concrete next action
"""


class AIEngineError(RuntimeError):
    pass


class ProductTriageEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-6-luna").strip() or "gpt-6-luna"

    @property
    def mode(self):
        return "openai" if self.api_key and OpenAI is not None else "demo"

    def analyze(self, issue):
        if self.mode == "openai":
            try:
                return self._analyze_with_openai(issue)
            except Exception as exc:
                raise AIEngineError(
                    "The AI provider request failed. Check the API key/model configuration."
                ) from exc
        return self._analyze_demo(issue)

    def _analyze_with_openai(self, issue):
        client = OpenAI(api_key=self.api_key)
        prompt = f"""
Triage this product issue.

Title: {issue['title']}
Description: {issue['description']}
Customer impact: {issue['customer_impact']}
Frequency: {issue['frequency']}
Platform: {issue['platform']}
Source: {issue['source']}
"""
        response = client.responses.create(
            model=self.model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        return normalize_result(json.loads(response.output_text.strip()))

    def _analyze_demo(self, issue):
        """Deterministic fallback for public demos without an exposed API key."""
        text = " ".join([
            issue["title"], issue["description"], issue["customer_impact"],
            issue["frequency"], issue["platform"],
        ]).lower()

        security_words = {"security", "breach", "exposed", "fraud", "unauthorized", "password"}
        outage_words = {"down", "outage", "unavailable", "cannot login", "can't login", "crash"}
        money_words = {"trade", "balance", "payment", "money", "order", "portfolio"}
        performance_words = {"slow", "latency", "delay", "seconds", "timeout"}

        if any(word in text for word in security_words):
            priority, impact, category, owner, confidence = "P0", "Critical", "Security", "Security", 92
            labels = ["security", "customer-impact", "urgent"]
        elif any(word in text for word in outage_words) and issue["frequency"] in {"Always", "Often"}:
            priority, impact, category, owner, confidence = "P1", "High", "Reliability", "Platform", 88
            labels = ["reliability", "customer-impact", "incident"]
        elif any(word in text for word in money_words):
            priority, impact, category, owner, confidence = "P1", "High", "Financial Experience", "Backend", 84
            labels = ["financial-data", "backend", "customer-impact"]
        elif any(word in text for word in performance_words):
            priority, impact, category, owner, confidence = "P2", "Medium", "Performance", "Backend", 82
            labels = ["performance", "latency", "backend"]
        else:
            priority, impact, category, owner, confidence = "P2", "Medium", "Product Defect", "Product", 72
            labels = ["product", "triage", "needs-review"]

        if issue["customer_impact"] == "Blocks core task" and priority == "P2":
            priority, impact = "P1", "High"
        if issue["customer_impact"] == "Minor inconvenience" and priority == "P1":
            priority, impact = "P2", "Medium"

        follow_up = []
        if issue["frequency"] in {"Unknown", "Rare"}:
            follow_up.append("How many users or sessions are affected?")
        if issue["customer_impact"] == "Unknown":
            follow_up.append("Does this block a core customer workflow?")
        if not re.search(r"\d", issue["description"]):
            follow_up.append("Is there a measurable latency, error-rate, or failure threshold?")

        return normalize_result({
            "priority": priority,
            "category": category,
            "owner_team": owner,
            "impact_level": impact,
            "confidence": confidence,
            "summary": f"{issue['title']} is best treated as a {category.lower()} issue with {impact.lower()} user impact.",
            "rationale": (
                f"The recommendation considers the reported customer impact ('{issue['customer_impact']}'), "
                f"frequency ('{issue['frequency']}'), and issue language. The evidence supports {priority} "
                "rather than automatically escalating to the highest severity."
            ),
            "next_action": f"Have the {owner} owner reproduce the issue, capture a measurable baseline, and confirm scope before committing the fix.",
            "labels": labels,
            "acceptance_criteria": [
                "The issue can be reproduced with documented steps before the fix.",
                "The reported customer-facing behavior no longer occurs after the fix.",
                "A regression test or verification step is added for the affected flow.",
            ],
            "follow_up_questions": follow_up,
        })


def normalize_result(result):
    required = {
        "priority", "category", "owner_team", "impact_level", "confidence",
        "summary", "rationale", "next_action", "labels", "acceptance_criteria",
        "follow_up_questions",
    }
    missing = required.difference(result)
    if missing:
        raise AIEngineError(f"AI response missing fields: {', '.join(sorted(missing))}")

    if result["priority"] not in {"P0", "P1", "P2", "P3"}:
        result["priority"] = "P2"
    if result["impact_level"] not in {"Critical", "High", "Medium", "Low"}:
        result["impact_level"] = "Medium"

    try:
        result["confidence"] = max(0, min(100, int(result["confidence"])))
    except (TypeError, ValueError):
        result["confidence"] = 50

    for field in ["labels", "acceptance_criteria", "follow_up_questions"]:
        if not isinstance(result[field], list):
            result[field] = []

    result["labels"] = [str(x).strip().lower() for x in result["labels"] if str(x).strip()][:5]
    result["acceptance_criteria"] = [str(x).strip() for x in result["acceptance_criteria"] if str(x).strip()][:5]
    result["follow_up_questions"] = [str(x).strip() for x in result["follow_up_questions"] if str(x).strip()][:4]

    for field in ["category", "owner_team", "summary", "rationale", "next_action"]:
        result[field] = str(result[field]).strip()
    return result
