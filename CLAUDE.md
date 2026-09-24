# CLAUDE.md — Agent Conventions for PropLaw

This file defines the rules and conventions the Claude Code agent must follow throughout this project. Read it before making any change to this codebase.

---

## Product Context

- PropLaw is a **consumer product for German homeowners**. It is not a developer tool and not a B2B product.
- The end user is someone like **Renate** (67, retired, low technical confidence) or **Tobias** (41, wants to be informed before talking to an architect).
- Every output the product generates must be:
  - Written in **plain German**
  - Include a **cited source** (paragraph, regulation name, jurisdiction)
  - End with a **concrete next action** for the user
- Never generate UI copy that sounds like a legal disclaimer. It should sound like a **knowledgeable friend explaining the rules**.

---

## Code Conventions

### Python

- All Python files must include a **module-level docstring** explaining what the file does.
- All functions over 20 lines must include a **docstring**.
- No hardcoded API keys — use environment variables loaded from `.env`. The `.env` file must never be committed.
- All API endpoints must include **input validation** (Pydantic) and return structured error messages:
  - **English** for developers (in the `detail` field)
  - **German** for end users (in the `user_message` field)

### JavaScript / React

- Components go in `propra/frontend/src/components/`.
- Frontend design rules (mobile-first, Tailwind, colours, typography) live in `propra/frontend/CLAUDE.md` and load automatically when working on frontend files.

---

## AI / Data Conventions

### Prompts

- Every LLM prompt must be stored as a `.txt` or `.md` file in `propra/prompts/`. **Never inline prompts in code.**
- Every prompt file must begin with a comment block containing:
  ```
  # WHAT: What this prompt does
  # INPUTS: What variables it expects
  # OUTPUT FORMAT: What structure it returns
  ```

### LLM Outputs

- All LLM outputs must be **validated against a Pydantic schema** before being passed to the frontend.
- **Confidence must never be set to `HIGH`** when B-Plan data is absent from the corpus.

### Knowledge Graph

- Every **node** must include: `type`, `jurisdiction`, `source_paragraph`, `text`
- Every **edge** must include: `relation`, `sourced_from`

---

## Testing Conventions

- Every API endpoint must have at least **one happy-path test** and **one error-path test** in `propra/tests/`.
- Every prompt must be tested against at least **5 sample inputs** before being used in the pipeline.
- KG queries must be tested against the **10 benchmark questions** defined in `propra/eval/benchmark.py`.

---

## Commands & Pitfalls

- Start: `uvicorn propra.main:app --reload` — **not** `api.main` as in the README.
- Tests: `PYTHONPATH=. pytest propra/tests/`, single tests with `-k`.
- Full check: `bash kontrolle.sh`.
- The package is called `propra`, the product is called PropLaw — intentional, do not rename.
- `propra/graph/*_section_edges.py` are generated — never edit them by hand.
- FAISS `source_file` and the KG prefix must be identical, otherwise GraphRAG does not apply.

---

## Git Workflow

- CI (`.github/workflows/ci.yml`) runs on every pull request **and** on every push to `main`.
- Direct pushes to `main` are allowed for small changes without behaviour change: docs, findings, config, comment-only fixes.
- Everything else goes through a branch and a pull request: refactors, features, dependency or tool version bumps, anything that changes behaviour.
- Before any push: `bash kontrolle.sh`, or at least `ruff check .` and the tests. The local ruff version must match the pin in `ci.yml`.
- A red CI run on `main` is fixed before any other work starts.
- Commit messages are English and follow Conventional Commits (`fix(F011): ...`, `docs(findings): ...`).
- Commit hashes cited in findings or logs are read from GitHub after the push, never from a local or cloud session.

Background: until 2026-09-24 CI ran on pull requests only. Five direct pushes to `main` went unchecked, and one of them (3fbba20) broke the lint step without anyone noticing.

---

## Language

- All developer-facing content in this repo is English: code, comments, docs, `FINDINGS.md`, this file, commit messages.
- User-facing product text stays German (see Product Context), as do the `user_message` fields.
- Benchmark queries and German legal terms (e.g. BbgBO, Verfahrensfreiheit) stay verbatim German — they are data, not prose.

---

## Findings & Day Planning

`propra/benchmark/results/FINDINGS.md` is the only list of open findings.
Every OPEN finding carries a `**Reviewed:**` field — the date it was last
looked at *and decided on*. Age = today minus Reviewed.

- Day planning draws from this file: at least one block per working day
  comes from the OPEN list, namely the oldest finding that fits the time.
- An OPEN finding unreviewed for more than 21 days must be scheduled or moved
  to `DEFERRED` — with a reason and a `Deferred until:` date.
- When a finding is **created**, the creating run sets `Reviewed:` to the
  creation date. That starts the ageing clock instead of hiding it.
- Every **later** change to `Reviewed:` is made only by the `/tagesplan` skill
  while Sebastian goes through the plan. Never by hand, never by an unattended
  run: a date set after the fact hides exactly the ageing that should stay
  visible.
- A finding is updated in the same commit that changes its state.
  Multi-step findings carry a `**Progress:**` block (see the header of
  `FINDINGS.md`).
- A Monday scheduled task reports overdue findings without touching the file.

Background: blocker B-01 was at the top of the audit from 2026-09-06 and was
fixed only thirteen days later. Six other findings sat for five months.
Writing things down achieves nothing on its own.

## What This Agent Must Never Do

- Never generate **legal advice** — always regulatory information with cited sources.
- Never return a **`HIGH` confidence verdict** when corpus coverage is incomplete.
- Never add **features outside the current epic scope** without flagging it first with a comment and asking.
- Never skip **mobile optimisation** on any UI component.
- Never **inline secrets or API keys** in code, prompts, or config files.
- Never commit the `.env` file.
