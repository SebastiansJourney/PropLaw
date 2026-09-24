# PropLaw — Repository Audit & Reset v7.0

**As of:** 2026-09-06 · **Replaces:** `docs/archive/roadmap/ROADMAP_v6_2_LBO-advisor.html`
**Analysed against:** `SebastiansJourney/PropLaw`, commit `8ec6204` on `main`
**Translated** from the German original on 2026-09-24. Content unchanged except for the corrections below.

**What changes compared to v6.2:** team of four becomes one person plus a set of agents; the capstone roadmap becomes a product roadmap; scope changes from "16 federal states" to "depth first"; hardening and cost control come before feature work.

## Corrections since 2026-09-06

- **B-02** describes the Render endpoint as owned by the project. That is wrong: the deployment belongs to a former teammate. The actual lever was the API key, which was revoked on 2026-09-21. See F012 in `propra/benchmark/results/FINDINGS.md`.
- **B-01** was fixed on 2026-09-19 (`ff48a74`): neither `faiss.index` nor `chunks.pkl` is versioned any more; both are built with `python -m propra.retrieval.rag build`.
- **Team (section 4):** the number of agents is not fixed at eight. Agents are added when a real task needs one, starting with `qa-reviewer`.
- Current status of all findings lives in `FINDINGS.md`, not in this document.

---

## 0. Conflicts

⚠️ **CONFLICT 01 — Timeline.** The project brief names 2026-04-02 as the deadline; today is 2026-09-06. Last substantive commit: 2026-04-01, followed only by a README rename on 2026-07-09. The repo has been idle for ~5 months, the bootcamp is completed. → Product roadmap, not a capstone roadmap.

⚠️ **CONFLICT 02 — Tech stack.** The project brief names LangGraph and Groq. Neither exists in the code. `assess.py` is a linear function chain without orchestration. v6.2 documents Groq → Anthropic correctly; LangGraph (F3, owner Matteo) was never built. The README additionally claims "LangChain (optional)" — not in `requirements.txt`.

⚠️ **CONFLICT 03 — Three API contracts.** `docs/api-contract.md` v0.4, `frontend/src/lib/api.ts` and the actual `fetch()` in `AdvisorPage.tsx` describe three different interfaces (`question` vs. `project_description`, `citations` vs. `cited_sources`, `next_actions` vs. `next_action`, lower vs. upper case for `confidence`).

## Decisions taken

| Field | Decision |
|---|---|
| Target picture | A real product with external users |
| Scope | Depth first — 1–2 federal states production-ready |
| Capacity | 5–15 h/week → 2-week sprints |
| Sebastian's role | Anchor / PM / CEO, sole merge authority |
| Budget | open, recommendation see section 5 |

---

## 1. Code health

**Key figures:** 233,071 lines of Python, of which 220,401 are generated (94.6 %). 98 tests green. Coverage of runtime modules 64 % (not 84 % — the CI figure is skewed by the generated files), `kg_retriever.py` at 22 %. 99 MB working tree, 36 MB `.git`.

### Blockers

- **B-01 — A fresh clone cannot produce an answer.** `faiss.index` (10 MB) is checked in, `chunks.pkl` is excluded by `.gitignore:20 *.pkl` (`graph.pkl` passes via an exception). The index is worthless without the chunk list.
- **B-02 — Public, unthrottled LLM endpoint.** `AdvisorPage.tsx` calls the hardcoded `https://proplaw-graphrag.onrender.com/api/assess`. No auth, no rate limit, no cost cap, no request logging. Two Anthropic calls per request.

### Dead code & artefacts (deletable, ~7 MB)

| Path | Size | Finding |
|---|---|---|
| `propra/frontend/src/lib/api.ts` | 121 lines | Fully mocked, imported by no component |
| `lib/vis-9.1.2/`, `lib/tom-select/`, `lib/bindings/` | 756 KB | Vendored JS from a pyvis export in the repo root |
| `data/data/` | 2.0 MB | Stray folder, incl. `BayBO_.rtf` (1.1 MB) |
| `check_structure.py` | 0 bytes | Empty |
| `propra/analytics/events.py` | 1 line | Docstring only — event logging does not exist |
| `propra/retrieval/kg_query.py` | 8 stmts | 0 % coverage, unreachable |
| `datasets/node inventory/*_v2.md` | 16 files | Never referenced; only `_fine` is read |
| `prompts/propose_edges.txt`, `rag_answer.txt` | 2 files | Loaded by no module |
| `graph/generate_bbgbo_section_edges.py` | — | Predecessor of the generic generator |
| `benchmark/results/*.csv` | 4.1 MB | Move out rather than delete |
| `package-lock.json` (root) | 86 B | Empty stub; the frontend additionally has two lockfiles |

### Technical debt

| ID | Finding |
|---|---|
| TD-01 | 220,000 lines of generated code checked in as `.py` (15 files, 10–17k lines each). They are data, not code → JSONL + loader |
| TD-02 | `sys.path` manipulation in four places. Measurable damage: coverage reports "propra.retrieval was never imported" |
| TD-03 | `api/__init__.py` imports `from main import app` → circular trap, works only by accident |
| TD-04 | Side effects on import: `_retriever = rag.Retriever()`, prompt file I/O, `sys.stdout.reconfigure()` in library modules |
| TD-05 | Jurisdiction filter as a post-filter with `k*50` overfetch — can silently return nothing for small states |
| TD-06 | Pickle as exchange format, incl. the `_ChunkUnpickler` `__main__` remap |
| TD-07 | Two retriever singletons → two embedding models in memory |
| TD-08 | Model names hardcoded (`claude-sonnet-4-6` ×4, `gpt-4o`, `gemini-2.0-flash`) |
| TD-09 | `.env.example` documents 2 unused variables and is missing 5 used ones |
| TD-10 | Directory name with a space: `propra/data/node inventory/` |
| TD-11 | `except Exception: return None` in the classifier — errors are invisible |
| TD-12 | README start command `uvicorn api.main:app` fails reproducibly; correct is `propra.main:app` |
| TD-13 | CI: `npm install` instead of `npm ci`, no deploy job, no Dockerfile, no coverage gate |
| TD-14 | Frontend sends `language`, `floors`, `inside_outside`, `postcode` — the schema drops them (`extra: ignore`). The language switch has no effect |
| TD-15 | Ruff on default rules only. With `F,E,I,UP,B,SIM,ARG`: 649 findings |

### Target structure

```
PropLaw/
├── proplaw/            # package rename propra → proplaw
│   ├── api/            # pure handlers, no __init__ re-export
│   ├── core/           # NEW: config.py, logging.py, deps.py
│   ├── orchestration/  # NEW: LangGraph
│   ├── retrieval/      # build.py, chunking.py, retriever.py (one singleton)
│   ├── kg/             # loader.py reads edges/*.jsonl
│   ├── schemas/ prompts/ tests/
├── tools/              # NEW: one-off scripts, not importable
├── datasets/           # NEW: node_inventory/, edges/, txt/
├── frontend/ docs/ evaluation/
└── Dockerfile · render.yaml · Makefile · pyproject.toml
```

Two core moves: one-off scripts out of the importable package, data out of the code.

---

## 2. Status quo

| ID | Feature (v6.2) | Status | Current state |
|---|---|---|---|
| F1 | RAG pipeline | partial | 6,564 vectors, Absatz-level chunking; does not run from a clone (B-01) |
| F2 | Knowledge graph | partial | 16 states generated, only Brandenburg curated; `kg_retriever` 22 % tested |
| F3 | LangGraph | **missing** | No routing, no retry, no confidence logic |
| F4 | Out-of-scope guard | **missing** | A tenancy law question is answered as a building law question |
| F5 | Dual language | UI only | Backend drops `language` (TD-14) |
| F6 | Frontend | running | Advisor wired; `PermitPage` (493 lines) without a backend call |
| F7 | PDF upload | **missing** | — |
| F8 | Evaluation | running | Own framework instead of RAGAS. **The strongest substance in the repo** |

**Success criteria against measurements:** latency target < 6 s, measured 17.5 s (RAG) / 19.5 s (GraphRAG) — missed by a factor of 3. Judge score 3.60/6 (from 2.55). Completion rate 94.9 % (4× HTTP 502). Trust rating 4.08/4.11 out of 5 — synthetic, not real.

**GraphRAG assessed honestly:** 49:22 in pairwise preference, but absolute deltas of only +0.03 to +0.07 on a 5-point scale at 2 s extra latency. A direction, not proof. As a product argument it does not hold up at present.

**Gaps to production readiness:** security (auth, rate limit, cost cap), operations (Docker, deploy config, logging, monitoring), performance (warm-up, caching, RAM), data (reproducible build, corpus versioning), legal (imprint, privacy policy, liability, RDG boundary), quality (regression tests, coverage gate, expert review), product (user analytics missing entirely).

---

## 3. Roadmap

**Phase 0 — Emergency brake** (Sprint 0, 1 week, ~6 h)
Close the endpoint + budget alert (B-02) · solve the `chunks.pkl` problem, make the index build reproducible (B-01) · fix README and `.env.example` · hosting / model decision.
*Why first:* as long as an endpoint that anyone can bill to you is open and nobody can start from a clone, every further hour is built on sand.

**Phase 1 — Clean-up & foundation** (Sprint 1–2, 4 weeks)
Deletion list · TD-01 (edges → JSONL) · TD-02/03/04 (import hacks, lifespan) · target structure + package rename · ruff rule set, `npm ci`, coverage gate 70 % · resolve the contract conflict (generate the API contract from OpenAPI, delete `api.ts`).
*Why:* feature work in this codebase carries a surcharge. At 5–15 h/week this pays off from sprint 3 — and agents work much more reliably in a structured repo.

**Phase 2 — Hardening for real users** (Sprint 3–4, 4 weeks)
Dockerfile + deploy config, staging/prod · rate limiting, request limit, token budget counter · structured logging, funnel events · latency below 6 s (prompt caching, Sonnet 5, shorter context) · `VITE_API_URL`, real error states · imprint, privacy policy, disclaimer, RDG boundary.
*Why before features:* 17–19 s and a 5 % error rate are measured. Whoever gets a 502 after 19 s does not come back.

**Phase 3 — Product core** (Sprint 5–6, 4 weeks)
F3 LangGraph (`guard → classify → retrieve → enrich → synthesise → validate`, retry, RAG fallback) · F4 out-of-scope guard (**a safety feature**) · F5 pass language through the schema · `kg_retriever` from 22 % to ≥ 70 %.
*Why now:* building LangGraph into today's `assess.py` would cement the import hacks.

**Phase 4 — Depth: finish Brandenburg** (Sprint 7–8, 4 weeks)
Work through and close F001–F006 · F004 corpus gap § 61 (verfahrensfreie Vorhaben — the most common lay question, currently the weakest answer) · retrieval regression suite in CI · spot-check Brandenburg edges, mark the other 15 states as "unreviewed" · 50-answer sample · **commission a human expert review**.
*Why depth before breadth:* 16 unreviewed states are 16× the same risk, not 16× the benefit.

**Phase 5 — Open & scale** (from Sprint 9)
Closed beta with 10–20 real users · funnel analysis · add states via the established pipeline · wire up or remove `PermitPage` · F7 PDF upload only on real user demand.

---

## 4. Team reset

Sumit, Nuria and Matteo have left. The roles are carried by subagents under `.claude/agents/`; Sebastian commissions them and is the only one who merges.

| Role | Agent | Responsibility | First task |
|---|---|---|---|
| Anchor (human) | **Sebastian** | Scope, prioritisation, decision log, budget, legal, sole merge | Hosting / model decision, budget cap |
| Backend / developer | `backend-dev` | FastAPI, schemas, LangGraph, package structure, import hygiene | B-01 reproducible index build |
| Data scientist / ML | `retrieval-scientist` | Chunking, embeddings, FAISS, benchmark, judge, regression suite | F002 missing judge scores |
| Knowledge engineer | `kg-engineer` | Inventories, edges, graph schema, traversal, maturity levels | TD-01 edges to JSONL |
| UI / UX | `ux-engineer` | React, Tailwind, i18n, mobile-first, loading states, a11y | `VITE_API_URL`, real error states |
| QA / review | `qa-reviewer` | Tests, ruff, coverage, PR review against CLAUDE.md — writes no feature code | Coverage gate + ruff rule set in CI |
| Expert review | `legal-qa` | Citation authenticity, relevance, verdict, scope boundary. **Does not replace human expert review** | 50-answer sample Brandenburg |
| Platform / DevOps | `devops` | Docker, deploy, CI/CD, secrets, rate limit, cost cap, monitoring | B-02 close the endpoint |
| Product / analytics | `product-analyst` | User tests, funnel, metrics, decision log, updates | Define funnel events |

**Operating model:** one agent, one branch, one PR — never two agents in the same file (the scopes above deliberately do not overlap). `CLAUDE.md` remains the contract, extended by the new folder structure, the rule "generated artefacts never as `.py`" and the write-scope boundaries. Weekly rhythm instead of a daily: Monday 30 min planning, Friday 30 min review and merge. `docs/DECISIONS.md` as written memory — no agent remembers last week. Benchmark regression as a recurring scheduled task.

---

## 5. Operating costs

Assumption per request: ~8,000 input and ~700 output tokens across two LLM calls.

| Option | Hosting/month | LLM at 500 req. | at 2,000 req. | Viable |
|---|---|---|---|---|
| A · Render Free (512 MB) | $0 | $13 | $50 | **no** — RAM insufficient, ~40 s cold start (F005) |
| B · Render Starter (512 MB) | $7 | $13 | $50 | **no** — same RAM problem |
| C · Render Standard (2 GB) + 1 GB disk | $25.25 | $13 | $50 | **yes — approx. $38–75/month** |

**Three levers before any budget increase:** Sonnet 4.6 → Sonnet 5 ($2/$10 instead of $3/$15 per MTok, ≈ ⅓ cheaper, one line — TD-08) · prompt caching for the system prompt (cache hit = 10 % of the input price) · shorter context (today up to 8 FAISS chunks plus KG nodes, without measuring how many of them improve the answer).

**RAM is the real cost driver.** Núria's March note "free tier is not enough" has its cause in the code: `sentence-transformers` loads a multilingual MiniLM into the process, plus the FAISS index and the 6 MB graph, potentially twice because of TD-07. Move embeddings to an API or a separate service → the app fits a 512 MB instance again ($7). Architecture decision for phase 2.

*Prices based on Anthropic's and Render's published list prices at the time of analysis.*

---

## 6. Risks

- **R-01 — RDG and liability (critical).** A product that tells lay people whether their building project is permissible sits close to the Legal Services Act (Rechtsdienstleistungsgesetz, RDG). `CLAUDE.md` draws the line correctly, the product shows it nowhere, and `ALLOWED` reads like an approval. Obtain a lawyer's assessment before public operation. No agent can resolve this.
- **R-02 — 15 unreviewed state KGs (high).** The edges carry the note "Review and adapt" in the generator itself. Only Brandenburg is reviewed. A visible maturity level per state is more honest and protective.
- **R-03 — Legal text versions not tracked (high).** The PDFs carry no version date in the repo, answers state none. Building codes get amended. Minimum: record the version date per law and output it in every citation.
- **R-04 — Synthetic tests are not user tests (medium).** 4.08/5 comes from an LLM simulating users; the analysis report itself says so explicitly. A good regression signal, not product validation.
- **R-05 — Agents do not replace domain expertise (medium).** The roster covers development, operations and QA. Not covered: the legal judgement whether an answer is correct, and the product decision whether anyone needs this product. A paid expert reviewer should be planned for early.
