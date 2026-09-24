# Benchmark results

20 permit-decision queries against Brandenburg (DE-BB, BbgBO), each run through
RAG and GraphRAG (40 rows per file), scored 0–6 by the LLM judge in
`propra/benchmark/judge_runner.py`. Methodology: `docs/benchmark_methodology_v2.1.md`.
Open questions about these runs are tracked in `FINDINGS.md` in this folder.

| File | Stage | RAG | GraphRAG | What changed before this run |
|---|---|---|---|---|
| `judged_baseline_20260327_0823.csv` | pre-redesign | 2.10 | 2.00 | Reference only: 9 of 20 queries were still definitional, not permit decisions |
| `judged_baseline_20260330_1404.csv` | **Stage 1** | 2.55 | 2.55 | Query set reframed to permit decisions (Q01, Q02, Q03, Q06, Q13, Q20) |
| `judged_baseline_20260330_1640.csv` | **Stage 2** | 3.35 | 3.55 | Absatz-level chunking; FAISS index ~3,613 → 6,564 vectors |
| `judged_baseline_20260330_2254.csv` | **Stage 3** | 3.20 | 3.60 | Directional KG traversal and `source_file` jurisdiction filter (F003) |

Means are over `total_final` per system, re-computed from the files on 2026-09-24.

Rules:
- Never re-run a stage in place. A new run gets a new timestamped file and a new row here.
- Raw runner output (`baseline_*.csv`) is not kept: the judged file contains every runner column plus the scores.
