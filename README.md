# ClaimBot AI

An AI-powered auto insurance claim triage assistant. Given a raw claim
description, ClaimBot determines the category, priority, assigned team, and
a cited reasoning — using a RAG pipeline (policy manual retrieval +
schema-enforced LLM tool-calling) rather than a black-box classifier.

All routing logic lives in a single function, `load_and_route()`, in
`model.py`. The Flask app, the pytest suite, and the batch UI runner are all
thin callers of that one function — none of them re-implement retrieval,
prompt construction, or validation independently.

## Table of contents

- [What it does](#what-it-does)
- [Deliverables](#deliverables)
- [Quick start (Docker — recommended)](#quick-start-docker--recommended)
- [Quick start (without Docker)](#quick-start-without-docker)
- [Running tests](#running-tests)
- [Architecture](#architecture)
  - [Why RAG, and why this scale](#why-rag-and-why-this-scale)
  - [Model choice and a mid-sprint provider swap](#model-choice-and-a-mid-sprint-provider-swap)
- [Reliability and failure handling](#reliability-and-failure-handling)
- [Team and category design](#team-and-category-design)
- [Known limitations](#known-limitations)
- [Project structure](#project-structure)
- [Engineering process and debugging log](#engineering-process-and-debugging-log)

## What it does

A customer submits a claim description in plain language. ClaimBot:

1. Retrieves the most relevant rules from a hand-authored insurance policy
   manual (via ChromaDB + sentence-transformer embeddings)
2. Constructs a prompt combining those rules with the claim
3. Calls an LLM with a schema-enforced tool call to produce a structured
   routing decision
4. Validates the output against a strict Pydantic schema
5. Persists the result to Postgres and displays it in a web UI

Output is always one of a fixed set of categories/teams/priorities — never
free-form text — enforced at two layers (LLM tool schema + Pydantic
validation), with automatic retry and graceful fallback on failure.

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Prompts that consistently return valid structured JSON | Done — tool-use schema + Pydantic validation, see `tests/test_routing.py` |
| 2 | Handle 3 edge cases (angry tone, very short, ambiguous) | Done — dedicated tests `test_m4s3`–`test_m4s5` in `test_routing.py` |
| 3 | A simple interface to test it | Done — Flask web UI: single-claim comparison, batch ticket runner, claim history view |
| 4 | Before/after: manual vs. AI routing time | Done — live timer in UI on every routed claim; manual time measured by timing real manual triage against the same claims |
| 5 | Demo 20 sample tickets | Done — 20-ticket picker built into the UI, runnable individually or as a batch |

## Quick start (Docker — recommended)

### Prerequisites
- Docker Desktop installed and running
- An OpenAI API key

### Setup

```bash
git clone <repo-url>
cd ClaimPilot
```

Create a `.env` file in the project root with your OpenAI API key:

OPENAI_API_KEY=your_openai_api_key_here


Ingest the policy manual into ChromaDB (one-time, before first run):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m chunker
```

Build and run everything (Flask + Postgres):

```bash
docker-compose up --build
```

Visit `http://127.0.0.1:5000`.

## Quick start (without Docker)

### Prerequisites
- Python 3.12+
- PostgreSQL installed locally
- An OpenAI API key

### Setup

```bash
git clone <repo-url>
cd ClaimPilot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with the following variables:

OPENAI_API_KEY=your_openai_api_key_here

DB_HOST=localhost

DB_PORT=5432

DB_NAME=claimbot

DB_USER=<your_postgres_user>

DB_PASSWORD=<your_postgres_password>

Create the database and ingest the policy manual:

```bash
createdb claimbot
python3 -m chunker
```

Run the app:

```bash
python3 app.py
```
Visit `http://127.0.0.1:5000`.

## Running tests

```bash
pytest tests/test_routing.py -v
```

55 tests covering structural reliability (valid JSON, all required fields,
across adversarial inputs including empty strings, non-English text, and
off-topic questions), correctness (expected category/priority/team per
claim), and all mission-required edge cases: angry tone, short/vague
messages, ambiguous claims, and priority defensibility.

## Architecture

```
                      Claim text
                          |
                          v
                    Embed claim
                          |
                          v
            ChromaDB similarity search
                          |
                          v
              Top-k relevant rules
                          |
                          v
      Prompt = system prompt + rules + claim
                          |
                          v
        LLM call (schema-enforced tool use)
                          |
                          v
          Pydantic validation of output
                   |            |
               valid          invalid / API failure
                   |                |
                   v                v
            Return result    Retry (up to 2x, backoff)
                   |                |
                   |                v (all retries fail)
                   |          Safe fallback:
                   |          "System Error" /
                   |          "Engineering / Retry Queue"
                   |                |
                   +--------+-------+
                            |
                            v
              Persist to Postgres + display in UI
```

### Why RAG, and why this scale

At roughly 15 policy rules, any vector database performs comparably the
choice of ChromaDB specifically was about zero-infrastructure local setup,
not retrieval performance at scale. Retrieval-augmented generation was
chosen over pure prompt-based few-shot examples so the policy manual can be
edited and re-ingested independently of the prompt/code, and so reasoning
can cite specific rules rather than relying purely on the model's own
judgment. Testing during development showed most routing failures traced
back to rule-wording ambiguity, not retrieval quality a tested finding,
not an assumption.

Retrieval depth (`k=8`) was chosen empirically, not assumed — testing at
k=3 and k=5 against the full test suite reproduced specific, real failures
(a claim losing its priority escalation, another falling through to
Insufficient Information entirely) that k=8 does not exhibit.

### Model choice and a mid-sprint provider swap

ClaimBot originally ran on Groq (Llama 3.3 70B) to stay within open-source
models. Mid-sprint, testing hit Groq's free-tier daily token cap (100K
TPD). Since the pipeline is provider-agnostic by design — retrieval, prompt
construction, and Pydantic validation are all independent of which LLM
provider is used — the swap to OpenAI's GPT-4o-mini required changing only
the client initialization in `model.py`, no other code changes. This is a
tested example of the architecture's provider independence, not a
hypothetical claim.

## Reliability and failure handling

- **JSON schema enforcement** — the LLM is forced to call a specific tool
  with a strict enum-constrained schema, not asked to "return JSON" via
  prompt instruction alone.
- **Pydantic validation** — a second, independent validation layer catches
  any malformed or out-of-schema response before it's trusted.
- **Retry with exponential backoff** — up to 2 retries (3 total attempts)
  on both API failures (rate limits, timeouts, disconnects) and schema
  validation failures.
- **Graceful fallback** — if all retries fail, the system returns a
  `"System Error"` / `"Engineering / Retry Queue"` result instead of
  crashing. This is deliberately distinct from `"Insufficient Information"`
  / `"Manual Review Team"`, since a system failure is not a content-review
  problem and shouldn't be triaged the same way.
- Tested against both an invalid API key and a simulated network
  disconnect (see `SIMULATE_DISCONNECT` env var in `model.py`).

## Team and category design

Routing decisions distinguish between three distinct "fallback" situations,
based on whether human review time is actually warranted:

- **`Insufficient Information` / `Manual Review Team`** — the message
  contains real, specific content, but is genuinely ambiguous or
  self-contradictory. Reserved only for cases where a human can actually
  make a judgment the model couldn't.
- **`Insufficient Information` / `Automated Response`** — the message has
  zero concrete reference to any claim, incident, or issue (e.g., "broken",
  "help"). A human couldn't do anything with these either beyond asking
  for more detail, so an automated reply is used instead of consuming
  reviewer time.
- **`Out of Scope` / `Automated Response`** — the message has no insurance
  relevance at all (e.g., a weather question).

This distinction was added after identifying that treating all vague input
as requiring human review would waste Manual Review Team's time on
messages a human could not act on any better than the model.

## Known limitations

- **Disputed third-party injury claims** are not specially flagged. A
  message like "the other driver claims neck injury but walked away fine"
  routes to Personal Injury per the injury/context rule, without surfacing
  the claimant's skepticism about the other party's claim in the reasoning.
- **No billing/coverage-dispute category.** Claims involving billing
  disputes (e.g., a towing company charging the customer for something the
  insurer should cover) route to the closest existing category (Claim
  Status Inquiry) rather than a dedicated path — the current taxonomy was
  designed around accident triage, not billing disputes.
- **Hit-and-run circumstances** aren't specifically surfaced in reasoning,
  even though this materially affects real claims handling.
- Consistency on genuinely borderline priority calls (e.g., ambiguous
  injury severity language) can vary slightly between runs, since the LLM
  is not fully deterministic even at low temperature.

All of the above were identified through deliberate adversarial and
real-use-case stress-testing, documented in full below.


## Project structure

```
ClaimPilot/
├── app.py                  Flask app, routes, Postgres persistence
├── model.py                Core routing pipeline (load_and_route)
├── chunker.py              Policy manual parsing + ChromaDB ingestion/retrieval
├── db.py                   Postgres connection and query helpers
├── policy_manual.md        The routing policy rules
├── utils/
│   ├── logger.py           Daily-rotated logging
│   └── const.py            MODEL, SYSTEM_PROMPT, ROUTE_CLAIM_TOOL schema
├── tests/
│   └── test_routing.py     Full pytest suite
├── templates/               Flask HTML templates
├── static/                  CSS
├── documentation.md         Full debugging/experiment log
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Engineering process and debugging log

This project's routing logic was hardened through five distinct testing
phases: baseline correctness testing, a design-level fix to prevent wasted
human-review time, boundary-tightening after live testing, deliberate
adversarial stress-testing (which surfaced a real false-fraud-accusation
bug before it could reach a demo), and validation against unfiltered,
realistic customer language. Every failure found was root-caused before
being fixed — not patched by trial and error.

The full log every test failure, its root cause, the fix applied, and
the re-test result is in `documentation.md`.