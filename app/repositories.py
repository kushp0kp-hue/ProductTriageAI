import json
from .database import get_db


class TriageRepository:
    @staticmethod
    def create(issue, result, mode):
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO triage_runs (
                title, description, customer_impact, frequency, platform, source,
                priority, category, owner_team, impact_level, confidence, summary,
                rationale, next_action, labels_json, acceptance_criteria_json,
                follow_up_questions_json, mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue["title"], issue["description"], issue["customer_impact"],
                issue["frequency"], issue["platform"], issue["source"],
                result["priority"], result["category"], result["owner_team"],
                result["impact_level"], result["confidence"], result["summary"],
                result["rationale"], result["next_action"], json.dumps(result["labels"]),
                json.dumps(result["acceptance_criteria"]),
                json.dumps(result["follow_up_questions"]), mode,
            ),
        )
        db.commit()
        return TriageRepository.get(cursor.lastrowid)

    @staticmethod
    def get(run_id):
        row = get_db().execute("SELECT * FROM triage_runs WHERE id = ?", (run_id,)).fetchone()
        return TriageRepository._deserialize(dict(row)) if row else None

    @staticmethod
    def list_recent(limit=8):
        rows = get_db().execute(
            "SELECT * FROM triage_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [TriageRepository._deserialize(dict(row)) for row in rows]

    @staticmethod
    def _deserialize(row):
        row["labels"] = json.loads(row.pop("labels_json"))
        row["acceptance_criteria"] = json.loads(row.pop("acceptance_criteria_json"))
        row["follow_up_questions"] = json.loads(row.pop("follow_up_questions_json"))
        return row
