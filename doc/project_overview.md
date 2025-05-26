# Project Overview

## 1 · Problem & Goal  
The task was to **build and deploy a Retrieval-Augmented-Generation (RAG) assistant** that, as example, can answer _exactly two_ factual questions about Promtior:

1. “What services does Promtior offer?”  
2. “When was the company founded?”

Anything outside those scopes must be politely refused.

---

## 2 · Approach

### 2.1 Establish the mental model  
1. **Map the stack** – LangChain + LangServe, OpenAI API, FastAPI, Chroma.  
2. **Visualise the flow** – ingestion → vector DB → guard-rail → LLM.  
3. Decide early that a **tiny web front-end** (plain HTML/CSS/JS) would be friendlier than a console bot and still keep the scope tiny.

### 2.2 Design decisions  
| Decision | Rationale |
| -------- | ---------- |
| **Split into `api/` and `ui/`** | Clear responsibility boundaries; easier to swap UI later. |
| **Pure vanilla UI** | No build tools or frameworks → almost zero cognitive / deploy overhead. |
| **`config.json` for all tunables** | One source of truth; transforms the codebase into a reusable template. |
| **Keep `db/` out of the repo (initially)** | Vector stores belong to the environment, not to VCS. |
| **Docker from day 1** | Identical local and cloud behaviour; Railway autodetects the file. |

---

## 3 · Implementation Logic

1. **`ingest.py`**  
   *Scrape* three public pages + an explicit founding-date note, **split** them, **embed** with OpenAI, **persist** a Chroma collection.

2. **`main.py`**  
   *Pre-compute* embeddings for the approved questions, exposing a cosine-similarity **allow-list guard** (`threshold = 0.85`).  
   If a question matches → feed canonical phrasing into a **ConversationalRetrievalChain**; else → return `refusal_text`.

3. **Front-end (`ui/`)**  
   Loads labels from `/ui/config.json`, shows a minimal chat window, adds “typing dots” feedback, posts to `/chat/invoke`.

4. **Container & Deploy**  
   The Dockerfile installs `api/requirements.txt`, copies the whole repo, launches Uvicorn on `$PORT`.  
   Railway build → open shell → `python api/ingest.py` → restart → done.

---

## 4 · Main Challenges & How I Solved Them

| Challenge | Fix |
| ----------| ----|
| **Rigid allow-list (exact string match).** | Added a vector-similarity gate: embed canonical phrasings once, embed the user query on the fly, pick the closest if `cos ≥ 0.85`. |
| **Exposing too many magic numbers & literals.** | Moved URLs, extra docs, model, k, threshold, refusal text, UI copy… into `config.json` for hot-swappable behaviour. |
| **Cloud replies were “I don’t know” while local worked.** | Discovered Railway container lacked `api/db/`; quick workaround: commit the small DB to the repo before deadline. |
| **Tight deadline vs. perfect CI/CD.** | Prioritised shipping a functional prototype; documented a future plan to rebuild `db/` automatically during deploy. |

---

## 5 · Outcome

* **Fully-functional prototype** answering the two Promtior questions with RAG, refusing anything else.  
* **Simple one-click Railway deploy** – only needs `OPENAI_API_KEY`.  
* **Extensible template** – swap `source_urls`, change allow-list, or upgrade the UI without touching core logic.

---

## 6 · Future Work

* Build `db/` automatically in CI/CD instead of committing it.  
* Add more Promtior topics and expand the semantic guard.  
* Instrument logging / tracing for observability.  
* Migrate the front-end to a lightweight framework if richer UX is required.  
* Upgrade dependencies (`langchain-x`, Chroma server mode, gpt-4o proper) once stable.

---

## 7 · Time Spent

A focused **week-end sprint (~2 days)** from blank repo to live prototype, including local iteration, debugging, and Railway deployment.
