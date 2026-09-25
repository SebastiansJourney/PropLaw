#!/usr/bin/env bash
# PropLaw — pre-push check.
#
#   bash kontrolle.sh
#
# Picks the repo's venv (or creates .venv), checks the test dependencies
# and then runs three checks: tests, app import, linter. Every Python call
# goes to the venv's interpreter by path, never to whatever `python` is
# first on PATH, so the global Python is never touched (F015).

set -uo pipefail
cd "$(dirname "$0")"

if grep -q $'\r' "$0" 2>/dev/null; then
  echo "This script has Windows line endings (CRLF)."
  echo "Fix it once, then run it again:"
  echo "    sed -i 's/\\r\$//' $(basename "$0")"
  exit 1
fi

if [ ! -d propra ] || [ ! -d .git ]; then
  echo "This does not look like the PropLaw repo."
  echo "Current directory: $(pwd)"
  exit 1
fi

# The venv's interpreter, by path: Scripts/python.exe on Windows,
# bin/python elsewhere. Empty if the directory has neither.
venv_python(){
  if   [ -x "$1/Scripts/python.exe" ]; then echo "$1/Scripts/python.exe"
  elif [ -x "$1/bin/python" ];         then echo "$1/bin/python"
  fi
}

# ─────────────────────────────────────────────────────────────────────
echo
echo "▸ Step 1 — virtual environment"

VENV_DIR=""
for d in .venv venv env; do
  if [ -n "$(venv_python "$d")" ]; then VENV_DIR="$d"; break; fi
done

if [ -z "$VENV_DIR" ]; then
  # A system Python is only needed to create the venv.
  SYS_PY=""
  for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)" 2>/dev/null; then
      SYS_PY="$c"; break
    fi
  done
  if [ -z "$SYS_PY" ]; then
    echo "  No venv found and no Python 3.11+ to create one."
    echo "  Install: https://www.python.org/downloads/  (tick 'Add to PATH' during setup)"
    exit 1
  fi
  echo "  No venv found. Creating .venv with $SYS_PY ($("$SYS_PY" --version 2>&1)), takes ~20 s..."
  "$SYS_PY" -m venv .venv || { echo "  Creating the venv failed."; exit 1; }
  VENV_DIR=.venv
fi

PY="$(venv_python "$VENV_DIR")"

# Guard: stop before any pip call unless PY really is a venv interpreter.
if ! "$PY" -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)" 2>/dev/null; then
  echo "  $PY is not a venv interpreter. Stopping before anything is installed."
  exit 1
fi
echo "  Using: $PY ($("$PY" --version 2>&1))"

if [ -n "${VIRTUAL_ENV:-}" ] && ! "$PY" -c "import os, sys; n = lambda p: os.path.normcase(os.path.realpath(p)); sys.exit(0 if n(sys.prefix) == n(os.environ['VIRTUAL_ENV']) else 1)" 2>/dev/null; then
  echo "  Note: VIRTUAL_ENV points to $VIRTUAL_ENV,"
  echo "        which is not this repo's venv. Using $VENV_DIR anyway."
fi

# ─────────────────────────────────────────────────────────────────────
echo
echo "▸ Step 2 — dependencies for the check"

# Only what the test suite needs, as pip-name:import-name pairs. faiss-cpu
# and sentence-transformers (pulls in torch, ~800 MB) are NOT needed: the
# tests mock retrieval. A real index build needs the full requirements.txt.
DEPS="pytest:pytest pytest-asyncio:pytest_asyncio fastapi:fastapi pydantic:pydantic httpx:httpx networkx:networkx joblib:joblib anthropic:anthropic openai:openai python-dotenv:dotenv"

# ruff must match the version CI pins (CLAUDE.md "Git Workflow").
RUFF_PIN=$(grep -oE 'ruff==[0-9][0-9.]*' .github/workflows/ci.yml | head -1)
if [ -z "$RUFF_PIN" ]; then
  echo "  No ruff==<version> pin found in .github/workflows/ci.yml."
  exit 1
fi

INSTALL=""
MISSING=""
for pair in $DEPS; do
  pkg="${pair%%:*}"; mod="${pair##*:}"
  if ! "$PY" -c "import $mod" >/dev/null 2>&1; then
    INSTALL="$INSTALL $pkg"; MISSING="$MISSING $pkg"
  fi
done

RUFF_HAVE=$("$PY" -m ruff --version 2>/dev/null | awk '{print $2}')
if [ "ruff==$RUFF_HAVE" != "$RUFF_PIN" ]; then
  INSTALL="$INSTALL $RUFF_PIN"
  MISSING="$MISSING $RUFF_PIN (have: ${RUFF_HAVE:-none})"
fi

if [ -n "$INSTALL" ]; then
  echo "  Missing:$MISSING"
  echo "  Installing into $VENV_DIR..."
  "$PY" -m pip install --quiet --upgrade pip
  # shellcheck disable=SC2086
  "$PY" -m pip install --quiet $INSTALL || { echo "  pip install failed."; exit 1; }
  echo "  Done."
else
  echo "  All present ($RUFF_PIN)."
fi

# ─────────────────────────────────────────────────────────────────────
echo
echo "▸ Step 3 — the checks"
echo

FAIL=0

# ── [1/3] Tests — hard gate ──────────────────────────────────────────
echo "  [1/3] Tests"
TESTOUT=$(PYTHONPATH=. "$PY" -m pytest propra/tests/ -q 2>&1)
echo "$TESTOUT" | tail -2 | sed 's/^/        /'
if echo "$TESTOUT" | grep -qE "^[0-9]+ passed"; then
  echo "        ✓ green"
else
  echo "        ✗ red — something is actually broken"
  FAIL=1
fi
echo

# ── [2/3] App import — hard gate ─────────────────────────────────────
echo "  [2/3] App import"
if PYTHONPATH=. "$PY" -c "import propra.main" >/dev/null 2>&1; then
  echo "        ✓ propra.main imports"
else
  PYTHONPATH=. "$PY" -c "import propra.main" 2>&1 | tail -3 | sed 's/^/        /'
  echo "        ✗ import fails"
  FAIL=1
fi
echo

# ── [3/3] Linter — comparison, not a gate ────────────────────────────
# `ruff check .` as a yes/no gate does not fit here: ~2,980 findings come
# from the generated *_section_edges.py, i.e. from data, not code
# (TD-01). What counts: did this change introduce NEW findings?
echo "  [3/3] Linter — comparison against main"
EXC='propra/graph/*_section_edges.py'
count(){ "$PY" -m ruff check . --exclude "$EXC" --output-format=concise 2>/dev/null | grep -c ':' ; }

NOW=$(count)
BASE="?"
if git rev-parse --verify -q main >/dev/null && git diff --quiet && git diff --cached --quiet; then
  HERE=$(git rev-parse --abbrev-ref HEAD)
  git stash list >/dev/null 2>&1
  if git checkout main -q 2>/dev/null; then
    BASE=$(count)
    git checkout "$HERE" -q
  fi
fi

echo "        ruff $("$PY" -m ruff --version | awk '{print $2}'), generated edges excluded"
if [ "$BASE" = "?" ]; then
  echo "        now: $NOW findings (no comparison with main —"
  echo "        uncommitted changes in the tree)"
else
  echo "        main: $BASE  →  now: $NOW"
  if [ "$NOW" -le "$BASE" ]; then
    echo "        ✓ no new findings"
  else
    echo "        ! $((NOW-BASE)) new findings — look at them:"
    echo "          $PY -m ruff check . --exclude '$EXC'"
  fi
fi

# ─────────────────────────────────────────────────────────────────────
echo
echo "───────────────────────────────────────────────"
if [ "$FAIL" -eq 0 ]; then
  echo "  All green. Ready to push."
else
  echo "  At least one check is red — see the output above."
fi
echo "───────────────────────────────────────────────"
echo
exit "$FAIL"
