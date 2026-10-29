from .ai_engine import ProductTriageEngine
from .repositories import TriageRepository

VALID_IMPACTS = {"Blocks core task", "Major degradation", "Minor inconvenience", "Unknown"}
VALID_FREQUENCIES = {"Always", "Often", "Sometimes", "Rare", "Unknown"}
VALID_SOURCES = {"Customer report", "Support ticket", "Internal QA", "Product analytics", "Engineering", "Other"}


class ValidationError(ValueError):
    pass


class TriageService:
    def __init__(self, engine=None):
        self.engine = engine or ProductTriageEngine()

    def analyze(self, payload):
        issue = self._validate(payload)
        result = self.engine.analyze(issue)
        return TriageRepository.create(issue, result, self.engine.mode)

    def _validate(self, payload):
        title = str(payload.get("title", "")).strip()
        description = str(payload.get("description", "")).strip()
        customer_impact = str(payload.get("customer_impact", "")).strip()
        frequency = str(payload.get("frequency", "")).strip()
        platform = str(payload.get("platform", "")).strip()
        source = str(payload.get("source", "")).strip()

        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters.")
        if len(description) < 20:
            raise ValidationError("Description must be at least 20 characters.")
        if customer_impact not in VALID_IMPACTS:
            raise ValidationError("Select a valid customer impact.")
        if frequency not in VALID_FREQUENCIES:
            raise ValidationError("Select a valid frequency.")
        if source not in VALID_SOURCES:
            raise ValidationError("Select a valid source.")
        if not platform:
            raise ValidationError("Platform is required.")

        return {
            "title": title,
            "description": description,
            "customer_impact": customer_impact,
            "frequency": frequency,
            "platform": platform,
            "source": source,
        }
