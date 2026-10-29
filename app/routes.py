from flask import Blueprint, jsonify, request
from .ai_engine import AIEngineError, ProductTriageEngine
from .repositories import TriageRepository
from .services import TriageService, ValidationError

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    engine = ProductTriageEngine()
    return jsonify({
        "status": "ok",
        "ai_mode": engine.mode,
        "model": engine.model if engine.mode == "openai" else None,
    })


@api.post("/triage")
def triage():
    payload = request.get_json(silent=True) or {}
    try:
        result = TriageService().analyze(payload)
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except AIEngineError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(result), 201


@api.get("/triage")
def recent_triage():
    try:
        limit = int(request.args.get("limit", "8"))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400
    limit = max(1, min(25, limit))
    return jsonify(TriageRepository.list_recent(limit))
