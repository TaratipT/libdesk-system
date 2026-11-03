# LibDesk: Library Resource & Policy Assistant

LibDesk is a library circulation desk assistant that helps users check borrowing regulations, calculate overdue fines, find book shelf locations, and check group study room availability.

The system uses an autonomous agent loop with tool calling, lexical vector search (RAG) with rule citations, benchmarked retrieval evaluation, and a streaming web interface built with FastAPI and Server-Sent Events (SSE).

---

## Features

- **Rule Search with Citations:** Searches through 25 library regulations and returns exact section citations (e.g., Chapter 2, Rule 2.1) alongside the answer.
- **Agent Loop with Tools:** Uses `gemma-4-E4B-it` to choose and run tools based on the user's question, stopping when the answer is complete or after a 5-turn safety limit.
- **Retrieval Evaluation:** Tested against a 30-query labeled test set to measure Recall@3, Precision@3, MRR, and out-of-scope rejection rates across baseline and tuned score thresholds.
- **Streaming Web Interface:** FastAPI backend streaming answers token-by-token to the browser using Server-Sent Events (SSE).
- **Session Modes:** Supports Guest mode for general public queries, plus student and faculty login to inspect personal borrowing records and fines.
- **Type Validation:** All tool inputs and agent responses are validated using Pydantic schemas.

---

## Agent & Tools

The agent runs an autonomous execution loop with allow-listed tools and two stop conditions:
1. **Completion:** Stops when the model returns a final text answer without requesting any further tool calls (`tool_calls` is empty).
2. **Turn Limit:** A hard ceiling of `max_turns = 5` stops execution if a tool produces unexpected output or loops.

### Available Tools

| Tool Name | Input Parameters | Description |
|---|---|---|
| `search_regulations` | `query: str` | Searches regulations and returns matched text with official citations. |
| `lookup_member` | `member_id: str` | Looks up member profile, active loans, due dates, and fine balances. |
| `calculate_overdue_fine` | `book_type, days_overdue, hours_overdue` | Calculates fines based on book category and applies the 500 THB cap. |
| `search_book_location` | `query: str` | Finds call numbers, floor, shelf coordinates, and book availability. |
| `check_study_rooms` | *(none)* | Returns room capacities and current reservation time slots. |

---

## Retrieval Evaluation Results

We evaluated the retrieval system using a labeled test set of **30 queries** (26 in-scope library questions and 4 out-of-scope questions). 

We compared a baseline configuration (`min_score = 0.0`) against our tuned threshold (`min_score = 0.18`):

| Metric | Baseline (`min_score = 0.0`) | Tuned (`min_score = 0.18`) | Notes |
|---|:---:|:---:|---|
| **Recall @ 3** | **96.15%** | **84.62%** | High coverage of relevant clauses maintained. |
| **Precision @ 3** | 32.05% | 28.21% | Filters down to the most relevant clauses. |
| **MRR** | **0.9423** | **0.8462** | The correct rule is ranked at position 1 or 2. |
| **Rejection Rate** | **0.00%** | **75.00%** | Successfully rejects off-topic queries instead of hallucinating. |

At `min_score = 0.0`, the system retrieved rules for every query, even completely unrelated ones (0% rejection). Setting `min_score = 0.18` rejected 75% of out-of-scope questions while preserving an 84.62% Recall@3 on actual library questions.

To reproduce the benchmark:
```bash
python eval.py
```

---

## Project Structure

```text
RealProject/
├── app/
│   ├── config.py          # Proxy settings and environment loading
│   ├── database.py        # Local datastores (members, catalog, study rooms)
│   ├── main.py            # FastAPI app, REST endpoints, and SSE route
│   ├── schemas.py         # Pydantic schemas for data validation
│   ├── agent/
│   │   ├── loop.py        # Agent loop (sync execution and async SSE streaming)
│   │   └── tools.py       # 5 allow-listed tool definitions
│   └── rag/
│       └── retriever.py   # Lexical vector search and citation extractor
├── data/
│   ├── library_rules.json # 25 library regulations across 11 chapters
│   ├── eval_set.json      # 30 labeled benchmark queries
│   └── eval_results.json  # Cached evaluation metrics
├── static/
│   ├── index.html         # Frontend user interface
│   ├── app.js             # Client logic and SSE stream reader
│   └── style.css          # UI styles
├── .env.example           # Environment template
├── eval.py                # Evaluation benchmark script
└── requirements.txt       # Project dependencies
```

---

## How to Run

### 1. Setup Environment
```bash
# Clone the repository
git clone <REPOSITORY_URL>
cd RealProject

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to create `.env`:
```bash
# Windows:
copy .env.example .env

# macOS / Linux:
cp .env.example .env
```

Open `.env` and set your credentials:
```env
OPENAI_API_KEY=your_proxy_key_here
OPENAI_BASE_URL=https://your-class-proxy-url/v1
MODEL_NAME=gemma-4-E4B-it
HOST=127.0.0.1
PORT=8000
```

### 3. Start the Web Server
```bash
python -m uvicorn app.main:app --port 8000 --reload
```
Open your browser at: `http://localhost:8000`
