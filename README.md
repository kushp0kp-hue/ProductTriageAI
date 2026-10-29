# ProductTriage AI

ProductTriage AI is an AI-assisted product-operations tool that turns raw software issues into structured triage recommendations for Product Owners.

Instead of returning a generic chat response, the app produces a repeatable decision artifact:

- priority (P0-P3)
- impact level
- recommended owner
- product/engineering category
- confidence score
- executive summary
- prioritization rationale
- suggested labels
- acceptance criteria
- recommended next action
- follow-up questions when evidence is missing

## Why I built it

Product teams receive issues through customer reports, support tickets, QA, analytics, and engineering. Those reports vary widely in quality.

The goal of ProductTriage AI is to turn inconsistent issue descriptions into a consistent first-pass product decision while keeping the final decision with a human Product Owner.

This project focuses on the intersection of AI product design, software engineering, product prioritization, structured outputs, and human-in-the-loop decision making.

## Demo modes

### OpenAI mode

When `OPENAI_API_KEY` is configured, the backend calls the OpenAI Responses API and asks the model to return a structured JSON triage result.

### Demo mode

When no API key is configured, the app uses a deterministic local rules engine.

This keeps the public portfolio demo usable without exposing credentials. The UI clearly labels which mode is active.

## Architecture

```text
Browser
   |
   v
Flask REST API
   |
   v
Validation / Service Layer
   |
   v
AI Triage Engine
   |               \
   |                \--> OpenAI Responses API
   |                 or
   |                \--> Local demo engine
   v
SQLite decision history
```

## Product workflow

1. A user submits a raw product issue.
2. The service validates the issue evidence.
3. The AI engine converts it into a structured triage recommendation.
4. The result is normalized into a predictable schema.
5. The decision is stored in SQLite for review/history.
6. The UI displays priority, rationale, owner, labels, acceptance criteria, and follow-up questions.

## Tech stack

- Python
- Flask
- OpenAI Responses API
- SQLite
- HTML / CSS / JavaScript
- GitHub Actions
- Gunicorn
- Render-ready deployment

## Project structure

```text
ProductTriageAI/
├── app/
│   ├── __init__.py
│   ├── ai_engine.py
│   ├── database.py
│   ├── repositories.py
│   ├── routes.py
│   └── services.py
├── static/
│   └── styles.css
├── templates/
│   └── index.html
├── tests/
│   ├── test_api.py
│   └── test_engine.py
├── .github/workflows/tests.yml
├── .env.example
├── render.yaml
├── requirements.txt
└── run.py
```

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python run.py
```

Open `http://127.0.0.1:5000`.

The application runs in demo mode if no API key is configured.

## Enable live AI

Copy `.env.example` to `.env` and add:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-6-luna
```

Never commit a real API key.

## API

### Health

```http
GET /api/health
```

### Analyze an issue

```http
POST /api/triage
```

Example:

```json
{
  "title": "Portfolio balances take several seconds to refresh after a trade",
  "description": "Customers report stale balances for 8-12 seconds after a successful trade.",
  "customer_impact": "Major degradation",
  "frequency": "Often",
  "platform": "Web",
  "source": "Customer report"
}
```

### Recent decisions

```http
GET /api/triage?limit=8
```

## Testing

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the test suite automatically on pushes and pull requests.

## Product design decisions

**Why structured output instead of free-form chat?** A Product Owner needs fields that can be compared across issues, rendered consistently, stored, and tested.

**Why confidence?** AI recommendations should not pretend to be certain.

**Why follow-up questions?** Missing product evidence should not be invented by the model.

**Why keep a demo engine?** The public project stays interactive without exposing API credentials.

**Why store history?** Product decisions benefit from traceability.

## Human-in-the-loop design

The tool is decision support, not an autonomous incident manager. The Product Owner remains responsible for confirming scope, validating impact, escalating incidents, and accepting or rejecting the recommendation.

## Next improvements

- user authentication
- persistent Postgres database
- approve/edit workflow for AI recommendations
- prompt/version tracking
- Jira or GitHub issue import
- evaluation dataset comparing AI recommendations with human triage
