"""Check that every state-to-corpus mapping in the codebase agrees (F009, F010).

The mapping "federal state -> corpus file stem" is currently held in six
places. Each one is imported here, never copied, and compared against the
ground truth on disk: the stems of ``propra/data/txt/*.txt``.

1. ``JURISDICTION_MAP``            propra/retrieval/rag.py
2. ``_STATE_REGISTRY``             propra/graph/build_graph.py
3. ``_CORPUS_MAP`` (ISO codes)     propra/benchmark/judge_runner.py
4. ``_CORPUS_MAP`` (state labels)  propra/benchmark/judge_runner.py
5. ``jurisdiction_from_filename``  propra/data/bulk_inventory.py
6. ``_TXT_PATH_OVERRIDES`` and ``discover_states``
                                   propra/data/audit_extraction_artifacts.py

``JURISDICTION_MAP`` is used as the join table (stem, ISO code, label); it is
itself checked against the files on disk first.

Why it matters: GraphRAG derives a KG node ID from FAISS chunk metadata
(``f"{source_file}_§{section}"``). If one mapping drifts, lookups for that
state miss silently and GraphRAG degrades to plain vector retrieval without
any error. That happened for Baden-Württemberg and Bremen until 2026-09-19.

These tests stay after the F010 refactor: once all six places derive from one
registry they pass trivially, and they catch anyone who reintroduces a copy.
"""

from pathlib import Path

import pytest

from propra.benchmark.judge_runner import _CORPUS_MAP
from propra.data.audit_extraction_artifacts import (
    _INVENTORY_DIR,
    _TXT_DIR,
    _TXT_PATH_OVERRIDES,
    discover_states,
)
from propra.data.bulk_inventory import jurisdiction_from_filename
from propra.graph.build_graph import _STATE_REGISTRY
from propra.graph.kg_retriever import _chunk_to_node_id
from propra.retrieval.rag import JURISDICTION_MAP, TXT_DIR

# --- ground truth and join table ---------------------------------------------

_TXT_STEMS = sorted(p.stem for p in Path(TXT_DIR).glob("*.txt"))

# (stem, ISO code, label) for every corpus file, including the MBO
_ALL = sorted(
    (stem, meta["code"], meta["label"]) for stem, meta in JURISDICTION_MAP.items()
)
# the 16 Bundesländer only
_STATES = [row for row in _ALL if row[1] != "DE-MBO"]

_STEM_BY_CODE = {code: stem for stem, code, _ in _ALL}
_REGISTRY_BY_CODE = {cfg["jurisdiction"]: cfg for cfg in _STATE_REGISTRY}


def _ids(rows):
    return [label for _, _, label in rows]


# --- 0. ground truth ---------------------------------------------------------


def test_corpus_has_17_files():
    """16 Bundesländer plus the MBO. Guards against an empty or partial checkout."""
    assert len(_TXT_STEMS) == 17, _TXT_STEMS


# --- 1. JURISDICTION_MAP (rag.py) --------------------------------------------


def test_jurisdiction_map_matches_corpus_files():
    """Every txt file is mapped, and every mapped stem exists on disk."""
    assert sorted(JURISDICTION_MAP) == _TXT_STEMS


def test_jurisdiction_map_codes_and_labels_are_unique():
    codes = [code for _, code, _ in _ALL]
    labels = [label for _, _, label in _ALL]
    assert len(set(codes)) == len(codes), codes
    assert len(set(labels)) == len(labels), labels


# --- 2. _STATE_REGISTRY (build_graph.py) -------------------------------------


def test_registry_covers_all_16_states():
    """The KG registry holds exactly the 16 Bundesländer (no MBO)."""
    codes = sorted(cfg["jurisdiction"] for cfg in _STATE_REGISTRY)
    assert len(codes) == 16, codes
    assert len(set(codes)) == 16, "duplicate jurisdiction in _STATE_REGISTRY"
    assert codes == sorted(code for _, code, _ in _STATES)


@pytest.mark.parametrize(("stem", "code", "label"), _STATES, ids=_ids(_STATES))
def test_registry_entry_matches_corpus_stem(stem: str, code: str, label: str):
    """name, prefix, source_suffix and inventory all derive from the same stem."""
    cfg = _REGISTRY_BY_CODE[code]
    assert cfg["name"] == stem, f"{label}: registry name '{cfg['name']}' != stem '{stem}'"
    assert cfg["prefix"] == f"{stem}_", f"{label}: prefix '{cfg['prefix']}'"
    assert cfg["source_suffix"] == stem, f"{label}: source_suffix '{cfg['source_suffix']}'"
    assert cfg["inventory"] == f"{stem}_node_inventory_fine.md", f"{label}: inventory '{cfg['inventory']}'"
    assert (_INVENTORY_DIR / cfg["inventory"]).is_file(), f"{label}: inventory file missing"


@pytest.mark.parametrize(("stem", "code", "label"), _STATES, ids=_ids(_STATES))
def test_faiss_stem_and_kg_prefix_yield_same_node_id(stem: str, code: str, label: str):
    """What GraphRAG derives at query time must equal what build_graph names the node."""
    cfg = _REGISTRY_BY_CODE[code]
    derived = _chunk_to_node_id({"source_file": stem, "source_paragraph": "§ 1 Anwendungsbereich"})
    expected = f"{cfg['prefix']}§1"
    assert derived == expected, (
        f"{label} ({code}): FAISS stem '{stem}' derives '{derived}', "
        f"KG prefix '{cfg['prefix']}' gives '{expected}'. GraphRAG misses this state."
    )


# --- 3. and 4. _CORPUS_MAP (judge_runner.py) ---------------------------------


@pytest.mark.parametrize(("stem", "code", "label"), _ALL, ids=_ids(_ALL))
def test_corpus_map_iso_key(stem: str, code: str, label: str):
    assert _CORPUS_MAP.get(code) == stem, f"{label}: _CORPUS_MAP['{code}'] = {_CORPUS_MAP.get(code)!r}"


@pytest.mark.parametrize(("stem", "code", "label"), _ALL, ids=_ids(_ALL))
def test_corpus_map_label_key(stem: str, code: str, label: str):
    assert _CORPUS_MAP.get(label) == stem, f"_CORPUS_MAP['{label}'] = {_CORPUS_MAP.get(label)!r}"


def test_corpus_map_has_no_stale_keys():
    """No entry for a state or stem that no longer exists."""
    expected_keys = {code for _, code, _ in _ALL} | {label for _, _, label in _ALL}
    assert set(_CORPUS_MAP) == expected_keys, set(_CORPUS_MAP) ^ expected_keys
    assert set(_CORPUS_MAP.values()) == set(_TXT_STEMS)


# --- 5. jurisdiction_from_filename (bulk_inventory.py) -----------------------


@pytest.mark.parametrize(("stem", "code", "label"), _ALL, ids=_ids(_ALL))
def test_jurisdiction_from_filename(stem: str, code: str, label: str):
    got = jurisdiction_from_filename(f"{stem}.txt")
    assert got == code, f"{label}: jurisdiction_from_filename('{stem}.txt') = '{got}', expected '{code}'"


# --- 6. audit_extraction_artifacts.py ----------------------------------------


def test_audit_discovers_exactly_the_16_states():
    """discover_states() reads inventory file names; they must match the corpus stems."""
    assert discover_states() == sorted(stem for stem, _, _ in _STATES)


@pytest.mark.parametrize(("stem", "code", "label"), _STATES, ids=_ids(_STATES))
def test_audit_resolves_the_corpus_file(stem: str, code: str, label: str):
    txt_name = _TXT_PATH_OVERRIDES.get(stem, f"{stem}.txt")
    assert Path(txt_name).stem == stem, f"{label}: audit override points to '{txt_name}'"
    assert (_TXT_DIR / txt_name).is_file(), f"{label}: audit would read missing file '{txt_name}'"
