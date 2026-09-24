# PropLaw — Benchmark Findings Log

**Project:** neuefische AIPM Bootcamp Capstone 2025/2026
**Corpus:** BbgBO (DE-BB) — Phase 1 Baseline
**Methodology:** docs/benchmark\_methodology\_v2.1.md

\---

## How to use this file

* One entry per finding. Assign sequential ID (F001, F002, ...).
* Status: OPEN / IN REVIEW / DEFERRED / CLOSED
* Reviewed: date an OPEN finding was last looked at. A stale Reviewed
  date is the signal, not noise.
* On creation, the run that adds a finding sets Reviewed to the date it
  was added. That starts the ageing clock instead of hiding it.
* Every later change to Reviewed is made by the /tagesplan skill during
  day planning — never by hand, and never by an unattended job.
* An OPEN finding unreviewed for more than 21 days must be scheduled
  into a day plan or moved to DEFERRED with a reason and a review date.
* Update status and add resolution when closed.
* Multi-step findings carry a **Progress:** block. One line per
  completed step: date, what changed, evidence. Evidence is a commit
  hash read from GitHub after the push, or a command and its output.
  A local hash that never reached GitHub is not evidence.
* A finding is updated in the same commit that changes its state.
* Reference finding IDs in CSV notes column for traceability.
* Commit this file with every benchmark run.

\---

## Open Findings

### F004 — Q13 Verfahrensfreiheit — retrieval misses § 61 BbgBO (corpus complete)

**Date:** 2026-03-26
**Status:** OPEN — corpus extraction issue
**Reviewed:** 2026-09-20
**Query:** Q13 — Wann ist ein Bauvorhaben verfahrensfrei?
**Finding:** Both RAG and GraphRAG scored Retrieval=0 for this query.
The BbgBO corpus does not contain sufficient content from the
verfahrensfreie Vorhaben list (§ 61 BbgBO equivalent). Top FAISS
score was 0.70 — retrieval fired but returned wrong context.
This is a corpus extraction gap, not a pipeline failure.
**Action:** Re-extract BbgBO §61 section. Verify chunk content
covers the full list of verfahrensfreie Vorhaben.
**Impact:** Q13 scores (2/6 both systems) understate system quality.
Will improve after corpus fix.
**Owner:** Sebastian

\---

### F005 — Q1 cold-start latency outlier

**Date:** 2026-03-26
**Status:** OPEN — known, document only
**Reviewed:** 2026-09-20
**Finding:** Q1 RAG retrieval\_ms = 37,877ms (vs 20-70ms for all
subsequent queries). This is the sentence-transformer model loading
on first FAISS call. Skews RAG mean retrieval\_ms significantly.
**Action:** Document in benchmark report. Exclude Q1 from latency
aggregates or note as cold-start outlier. Consider warming the model
before benchmark runs in future.
**Impact:** Mean RAG retrieval\_ms is inflated. Real retrieval latency
is 20-70ms after warm-up.
**Measurement 2026-09-21:** The cold start measured in production is
82.9 s, not the roughly 40 s from the benchmark. The benchmark figure
covers only loading the embedding model, not waking up the sleeping
Render instance. See F012.
**Owner:** Sebastian (documentation only)

\---

### F006 — Q11 GraphRAG +3 over RAG — classification layer effect

**Date:** 2026-03-26
**Status:** DEFERRED — until pitch preparation
**Deferred until:** 2026-11-02
**Reviewed:** 2026-09-20
**Reason:** The original hypothesis (delta without KG chunks =
classifier effect) can no longer be tested on the current pipeline —
Q11 scores GraphRAG 4/6 vs RAG 2/6 with 31 KG chunks in Stage 3. The
underlying question remains open and is the more important one: does
GraphRAG contribute measurably? Audit v7.0 measures +0.03 to +0.07 on
a 5-point scale at +2 s latency, 49:22 in 71 pairwise comparisons —
a direction, not proof. Reframe for pitch preparation using the
Stage 3 data as KG evidence. If no pitch is scheduled by that date,
decide again instead of deferring further.
**Query:** Q11 — Welche Zusammenhänge bestehen zwischen
Brandschutzanforderungen und der Gebäudeklasse?
**Finding:** GraphRAG scored 6/6 vs RAG 3/6 on this cross-concept
query despite KG chunks = 0. The delta must come from the goal
classification step (kg\_query.query\_by\_category) influencing FAISS
retrieval context or the synthesis prompt. This is the strongest
single piece of evidence for KG architectural value in this run.
**Action:** Investigate what the classifier returned for Q11 and
how it affected retrieval. Document as pitch evidence.
**Impact:** Positive. Strengthens dual-retrieval hypothesis even
before KG enrichment is fully active.
**Owner:** Sebastian + Sumit

\---

### F010 — State-to-corpus-filename mapping hardcoded in six places

**Date:** 2026-09-19
**Status:** OPEN — refactor required
**Reviewed:** 2026-09-19
**Finding:** The mapping Bundesland -> corpus file stem is maintained
independently in six places: JURISDICTION\_MAP in retrieval/rag.py,
\_STATE\_REGISTRY in graph/build\_graph.py, \_CORPUS\_MAP in
benchmark/judge\_runner.py (both the ISO-code and the plain-label
variant), jurisdiction\_from\_filename in data/bulk\_inventory.py, and
data/audit\_extraction\_artifacts.py together with its test. Any rename
must be applied to all six by hand; F009 is what happens when one of
them drifts. This is the same class of defect as F003 (FAISS metadata
and KG attributes agreeing only by convention, with no single source of
truth). test\_prefix\_alignment.py covers only the first two.
**Action:** Introduce one canonical registry (stem, ISO code, label,
KG prefix) and derive the other five from it. The finding stays OPEN
until this refactor is merged; a test alone does not close it.
**Impact:** Root cause of F009. Until fixed, every future corpus
rename or new state carries the same silent-mismatch risk.
**Progress:**
- 2026-09-19 · fdb9702 · BW and HB prefixes aligned by hand in all six
  places (F009).
- 2026-09-19 · test\_prefix\_alignment.py added; asserts only
  JURISDICTION\_MAP and \_STATE\_REGISTRY (2 of 6).
- 2026-09-23 · Extension of the test to all six sources was written in a
  cloud session (local hash e8f6d4b) but never reached GitHub; lost with
  `git reset --hard origin/main`. Evidence: commit not in the fork,
  test file on main still imports only the two maps. Still 2 of 6.
**Owner:** Sebastian

\---

### F011 — ruff version drift: local 0.16.6, CI 0.15.7

**Date:** 2026-09-19
**Status:** OPEN — in progress
**Reviewed:** 2026-09-19
**Finding:** ruff 0.16.x widened its default rule set (UP, I, SIM, B,
FLY, BLE, ...). ci.yml and .pre-commit-config.yaml pin ruff to 0.15.7,
the local environment runs 0.16.6. The earlier count of 89 findings is
superseded, and so is the figure of 3,858 from the 2026-09-23 session
(measured outside the repo configuration). Measured on main 3fbba20
with the repo's pyproject.toml: ruff 0.16.6 reports 40 findings
(17 FLY002, 9 BLE001, 4 B017, 3 DTZ, 2 ISC004, 5 SIM/RUF/PLW);
ruff 0.15.7 reports 5 x E402.
**Cause of the regression:** 3fbba20 ran `ruff check --fix` with 0.16.6.
That removed 10 `# noqa: E402` comments which 0.16.6 treats as unused
but 0.15.7 still needs. With the CI pin, `ruff check .` now fails on
main (propra/api/\_\_init\_\_.py, propra/api/assess.py,
propra/benchmark/benchmark\_runner.py x2,
propra/tests/test\_synthetic\_user\_test.py). The commit message
says 186 fixes; the actual diff touches 31 files.
**Action:** (1) Restore green CI: either put the removed noqa comments
back, or bump the pin to 0.16.6 in ci.yml and .pre-commit-config.yaml
and resolve the 40 findings in the same PR. (2) Local ruff must always
match the pin. (3) Fix the 9 BLE001 first; FLY002 is optional.
**Impact:** Lint debt only, no runtime impact. The 40 findings stay
invisible until the pin is bumped.
**Progress:**
- 2026-09-19 · a78cf94 · ruff pinned to 0.15.7 everywhere, generated
  section edges excluded via pyproject.toml.
- 2026-09-23 · 3fbba20 · auto-fix with ruff 0.16.6, 31 files. Introduced
  the E402 regression described above.
- 2026-09-24 · Action (1) done via the first option: the 10 removed noqa
  comments restored in 6 files, local ruff set to 0.15.7 to match the
  pin. Evidence: `ruff check .` with 0.15.7 reports "All checks passed!".
  The commit is the one that adds this line.
**Owner:** Sebastian

\---

## Closed Findings

### F013 — Backend URL hardcoded in the frontend

**Date:** 2026-09-21
**Status:** CLOSED — resolved 2026-09-23
**Reviewed:** 2026-09-21
**Finding:** propra/frontend/src/pages/AdvisorPage.tsx calls the
Render URL hardcoded (line 423,
https://proplaw-graphrag.onrender.com/api/assess). The address belongs
in VITE\_API\_URL so that local, staging and production environments
can be told apart without a code change. As long as it is in the code,
the frontend necessarily points to the third-party deployment from
F012.
**Action:** Switch the call to VITE\_API\_URL; set the variable in .env
and in the deployment configuration. Listed in Audit v7.0 as the first
task of the ux-engineer.
**Impact:** No switching of environments without a rebuild; couples the
frontend to F012.
**Resolution:** AdvisorPage.tsx:423 reads `import.meta.env.VITE_API_URL`
with fallback http://localhost:8000. propra/frontend/.env.example
documents the variable. propra/frontend/src/test/api-url.test.ts
asserts that the Render address is not in the code and that the
variable is used. `grep -rn onrender propra/frontend/src` only matches
the test itself. The second part of the action (set the variable in
the deployment configuration) does not apply yet: there is no own
deployment. It belongs to the deploy work in Audit v7.0 phase 2.
**Progress:**
- 2026-09-21 · a72dea0 · Finding created (PR #4).
- 2026-09-23 · 23e4aec · URL switched to VITE\_API\_URL, .env.example
  and Vitest test added.
**Owner:** Sebastian (ux-engineer)

\---

### F012 — Anthropic key running in a third-party deployment

**Date:** 2026-09-21
**Status:** CLOSED — resolved 2026-09-21
**Reviewed:** 2026-09-23
**Finding:** The Render service proplaw-graphrag was deployed by a
former teammate during the capstone phase. Sebastian has no access to
this service: he cannot see its configuration or logs and cannot shut
it down. The API key stored there belongs to his Anthropic account, so
third-party load runs on his bill without him being able to see or
limit it. The service is demonstrably reachable: on 2026-09-21 a POST
to /api/assess answered 422 after 82.9 s, so the endpoint still
accepts requests (cold start, see F005). The key was never in the
repo: git log --all -S"sk-ant-" returns no match, .env is in
.gitignore.
**Correction to Audit v7.0:** Audit v7.0 describes the endpoint under
blocker B-02 as owned by the project. That is demonstrably wrong — the
deployment belongs to the former teammate, not to this project. The
audit file itself stays unchanged; this line is the correction.
**Action:** Revoke the key in the Anthropic account, create a new key
and keep it only in the local .env. Inform the former teammate first
so her service does not fail without notice.
**Impact:** Until revocation, a key under third-party control is in
use, and Sebastian can neither see nor stop its usage.
**Resolution:** Key revoked on 2026-09-21, former teammate informed.
New key set up locally in .env. API test successful: POST /api/assess
returns HTTP 200 with a complete AssessmentResponse.
**Progress:**
- 2026-09-21 · a72dea0 · Finding created (PR #4).
- 2026-09-21 · Key revoked, former teammate informed, new key in .env.
- 2026-09-23 · ab7d9fe · Finding closed.
**Owner:** Sebastian

\---

### F001 — Q18 GraphRAG 0/6 suspicious score

**Date:** 2026-03-26
**Status:** CLOSED — superseded 2026-09-20
**Query:** Q18 — Welche Rolle spielen Rettungswege im Brandschutz?
**Finding:** GraphRAG scored 0/6 (Retrieval=0, Reasoning=0, Grounding=0).
Answer content is identical to RAG answer (KG chunks = 0 for this run,
meaning both systems received the same context and prompt). A 0/6 score
is inconsistent with identical content scoring 6/6 for RAG. Likely a
judge API error or empty response during the GPT-4o judge run.
**Action:** Re-run judge\_runner.py on Q18 GraphRAG row specifically.
Expert review required before including this score in aggregates.
**Impact:** Q18 GraphRAG excluded from current mean totals.
**Resolution:** Superseded. The 0/6 was a judge artefact of the 2026-03-26 run.
In Stage 3 (judged\_baseline\_20260330\_2254.csv, commit ae0f4db) Q18
scores 4/6 for both RAG and GraphRAG; the 2026-03-26 run is no longer
the basis of any aggregate. No expert review needed. Closed during
day planning 2026-09-20.
**Owner:** Matteo (expert validation)

\---

### F002 — 3 missing judge scores (API timeout)

**Date:** 2026-03-26
**Status:** CLOSED — superseded 2026-09-20
**Affected rows:** Q5 GraphRAG, Q14 RAG, Q14 GraphRAG, Q16 GraphRAG
**Finding:** Judge runner failed to score these rows during the
2026-03-26 run. Likely Anthropic/OpenAI API timeout or rate limit.
The runner's resume support means re-running will skip already-scored
rows and only fill the missing ones.
**Action:** Re-run: python -m benchmark.judge\_runner benchmark/results/judged\_baseline\_20260326\_1357.csv
**Impact:** Missing rows excluded from aggregates. RAG mean based on
19/20 rows, GraphRAG mean based on 16/20 rows.
**Resolution:** Superseded by later runs. Source: judged\_baseline\_20260330\_2254.csv
(Stage 3), 40/40 rows judged (total\_draft populated, no gaps). The
2026-03-26 CSV was not backfilled and is not used in aggregates.
Closed during day planning 2026-09-20.
**Owner:** Sebastian

\---

### F003 — KG enrichment inactive (0 chunks for all queries)

**Date:** 2026-03-26
**Status:** CLOSED — resolved in Stage 2/3, closed 2026-09-20
**Finding:** get\_related\_chunks() returned 0 KG-derived chunks for
every query in the DE-BB run. Root cause: source\_paragraph string
matching between FAISS chunk metadata and graph node attributes is
not connecting. FAISS chunks use formats like "§ 6 BbgBO" while graph
nodes may use slightly different formats. As a result, RAG and
GraphRAG answers are identical for this entire run — the GraphRAG
vs RAG delta cannot be meaningfully measured yet.
**Action:** Sumit to investigate source\_paragraph format alignment
between rag.py chunk metadata and kg\_retriever.py node matching logic.
**Impact:** RAG vs GraphRAG comparison is invalid for this run.
GraphRAG scores reflect pure FAISS retrieval, not KG enrichment.
**Resolution:** Resolved in Stage 2/3 (commits b0caa2e, ae0f4db). Source:
judged\_baseline\_20260330\_2254.csv, column kg\_chunks\_added —
GraphRAG receives 5–35 KG chunks per query there, vs 0 in this run.
Lineage: F003 (KG enrichment silent for all of DE-BB,
source\_paragraph format mismatch) → F009 (same symptom, limited to
DE-BW/DE-HB, FAISS stem vs KG prefix; fixed 2026-09-19, guarded by
test\_prefix\_alignment.py) → F010 (root cause class: state-to-corpus
mapping kept in six places without a single source of truth; OPEN).
The residual risk of F003 lives on in F010. Closed during day
planning 2026-09-20.
**Owner:** Sumit

\---

### F007 — GraphRAG latency incorrectly measured (fixed)

**Date:** 2026-03-26
**Status:** CLOSED — fixed 2026-03-26
**Finding:** benchmark\_runner.py was measuring retrieval latency only,
not full pipeline latency. Two compounding bugs: (1) timer stopped
before LLM synthesis call, (2) GraphRAG FAISS call was cache-warm
after prior RAG call, causing \~44ms mean vs RAG \~769ms.
**Resolution:** Split into retrieval\_ms (retrieval only) and total\_ms
(full pipeline). Timer now wraps full retrieval + synthesis block.
Committed to feature/benchmark-runner-v2.
**Owner:** Sebastian

\---

### F008 — assess.py k=5 (updated to k=8)

**Date:** 2026-03-26
**Status:** CLOSED — fixed 2026-03-26
**Finding:** Production assess.py used k=5 for FAISS retrieval.
Annex-heavy and exception-heavy queries (e.g. Q13 Verfahrensfreiheit)
need more chunks to cover list-item content spread across multiple
chunks. k=8 increases coverage at negligible cost.
**Resolution:** k updated to 8 in assess.py and benchmark\_runner.py.
Committed to feature/benchmark-runner-v2.
**Owner:** Sebastian

\---

### F009 — FAISS/KG prefix misalignment for BW and HB (fixed)

**Date:** 2026-09-19
**Status:** CLOSED — fixed 2026-09-19
**Finding:** For Baden-Württemberg and Bremen the FAISS source\_file
stem (BauO\_BW, LBO\_HB) did not match the KG node prefix (BW\_LBO\_,
BremLBO\_). kg\_retriever.\_chunk\_to\_node\_id() derives the node ID as
f"{source\_file}\_§{section}", so every KG lookup for these two states
missed and GraphRAG silently degraded to plain FAISS retrieval —
the same symptom as F003, limited to DE-BW and DE-HB. The other 14
states were aligned.
**Resolution:** FAISS side aligned to the KG side (BW\_LBO and
BremLBO are the official abbreviations): txt files renamed via git mv,
JURISDICTION\_MAP in rag.py, \_CORPUS\_MAP in judge\_runner.py,
bulk\_inventory.py and audit\_extraction\_artifacts.py updated, FAISS
index rebuilt (6564 vectors). Regression test
propra/tests/test\_prefix\_alignment.py checks all 16 states by joining
JURISDICTION\_MAP and \_STATE\_REGISTRY on the ISO code and running
\_chunk\_to\_node\_id() against the registry prefix. On
chore/claude-setup.
**Owner:** Sebastian

\---

*Last updated: 2026-09-20 — day planning: F001, F002, F003 closed (superseded by Stage 3), F006 deferred until 2026-11-02, F004 and F005 scheduled*
