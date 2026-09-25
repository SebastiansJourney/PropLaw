"""Check that every state-to-corpus mapping agrees with one registry (F009, F010).

``propra/jurisdictions.py`` is the single source of truth for which corpus file
belongs to which jurisdiction. These tests check two things:

1. The registry matches the files on disk (raw PDFs, txt files, inventories).
2. Every module that used to keep its own table now equals what the registry
   produces. Each module is imported, never copied:

   - ``JURISDICTION_MAP``            propra/retrieval/rag.py
   - ``_STATE_REGISTRY``             propra/graph/build_graph.py
   - ``_CORPUS_MAP`` (ISO + labels)  propra/benchmark/judge_runner.py
   - ``jurisdiction_from_filename``  propra/data/bulk_inventory.py
   - ``_STATE_CONFIGS``              propra/data/generate_lbo_inventory.py
   - ``PDFS``                        propra/data/bulk_extract.py
   - ``_TXT_PATH_OVERRIDES`` and ``discover_states``
                                     propra/data/audit_extraction_artifacts.py
   - ``EXPECTED_STATES``             propra/eval/graph_spot_check.py
   - ``_full_lbo_name``              propra/data/draft_inventory.py
   - ``GERMAN_STATES``               propra/schemas/situation.py

Per-state lists that are not mappings (audit thresholds, one-off script
subsets) may stay hand-written, but their keys must be registry stems.

Why it matters: GraphRAG derives a KG node ID from FAISS chunk metadata
(``f"{source_file}_§{section}"``). If one mapping drifts, lookups for that
state miss silently and GraphRAG degrades to plain vector retrieval without
any error. That happened for Baden-Württemberg and Bremen until 2026-09-19.

A new module that maps states to corpus files must derive from the registry
and be added here. Keeping a second hand-written table is a review finding.
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
from propra.data.bulk_extract import PDFS
from propra.data.bulk_inventory import jurisdiction_from_filename
from propra.data.draft_inventory import _full_lbo_name
from propra.data.fix_flat_inventories import STATES as FIX_FLAT_STATES
from propra.data.generate_lbo_inventory import _STATE_CONFIGS
from propra.graph.build_graph import _STATE_REGISTRY
from propra.eval.graph_spot_check import EXPECTED_STATES
from propra.eval.kg_audit import _EXPECTED_ANCHORS
from propra.graph.kg_retriever import _chunk_to_node_id
from propra.jurisdictions import JURISDICTIONS, STATES, by_code, by_label, by_stem
from propra.retrieval.rag import JURISDICTION_MAP, TXT_DIR
from propra.schemas.situation import GERMAN_STATES

_DATA = Path(TXT_DIR).parent
_RAW_DIR = _DATA / "raw"

_ALL = [pytest.param(j, id=j.label) for j in JURISDICTIONS]
_STATE_PARAMS = [pytest.param(j, id=j.label) for j in STATES]


# --- registry against the files on disk --------------------------------------


def test_registry_has_16_states_and_the_mbo():
    assert len(JURISDICTIONS) == 17
    assert len(STATES) == 16
    assert [j.code for j in JURISDICTIONS if not j.is_state] == ["DE-MBO"]


def test_registry_keys_are_unique():
    for field in ("stem", "code", "label"):
        values = [getattr(j, field) for j in JURISDICTIONS]
        assert len(set(values)) == len(values), f"duplicate {field}: {values}"


def test_registry_lookups_round_trip():
    for j in JURISDICTIONS:
        assert by_stem(j.stem) is j
        assert by_code(j.code) is j
        assert by_label(j.label) is j


def test_registry_matches_txt_files():
    """Every txt file has a registry entry, and every entry has a txt file."""
    on_disk = sorted(p.stem for p in Path(TXT_DIR).glob("*.txt"))
    assert on_disk == sorted(j.stem for j in JURISDICTIONS)


def test_raw_pdfs_are_named_after_their_stem():
    """data/raw/<stem>.pdf for every entry, and no other PDF in data/raw.

    The extension is compared case-insensitively: MBO.PDF keeps its upper-case
    extension, because a case-only rename fails on Windows file systems.
    """
    on_disk = sorted(p.stem + ".pdf" for p in _RAW_DIR.iterdir() if p.suffix.lower() == ".pdf")
    assert on_disk == sorted(f"{j.stem}.pdf" for j in JURISDICTIONS)


@pytest.mark.parametrize("j", _STATE_PARAMS)
def test_state_has_fine_inventory(j):
    assert (_INVENTORY_DIR / f"{j.stem}_node_inventory_fine.md").is_file()


# --- rag.JURISDICTION_MAP ----------------------------------------------------


def test_rag_jurisdiction_map_is_derived():
    assert JURISDICTION_MAP == {j.stem: {"code": j.code, "label": j.label} for j in JURISDICTIONS}


# --- build_graph._STATE_REGISTRY ---------------------------------------------


def test_build_graph_registry_is_derived_and_ordered():
    assert [cfg["name"] for cfg in _STATE_REGISTRY] == [j.stem for j in STATES]


@pytest.mark.parametrize("j", _STATE_PARAMS)
def test_build_graph_registry_entry(j):
    cfg = next(c for c in _STATE_REGISTRY if c["name"] == j.stem)
    assert cfg == {
        "name": j.stem,
        "full_name": j.full_name,
        "inventory": f"{j.stem}_node_inventory_fine.md",
        "prefix": f"{j.stem}_",
        "source_suffix": j.stem,
        "jurisdiction": j.code,
    }


@pytest.mark.parametrize("j", _STATE_PARAMS)
def test_faiss_stem_and_kg_prefix_yield_same_node_id(j):
    """What GraphRAG derives at query time must equal what build_graph names the node."""
    cfg = next(c for c in _STATE_REGISTRY if c["name"] == j.stem)
    derived = _chunk_to_node_id({"source_file": j.stem, "source_paragraph": "§ 1 Anwendungsbereich"})
    assert derived == f"{cfg['prefix']}§1", (
        f"{j.label}: FAISS stem '{j.stem}' derives '{derived}', "
        f"KG prefix '{cfg['prefix']}'. GraphRAG misses this state."
    )


# --- judge_runner._CORPUS_MAP ------------------------------------------------


def test_judge_corpus_map_is_derived():
    expected = {j.code: j.stem for j in JURISDICTIONS} | {j.label: j.stem for j in JURISDICTIONS}
    assert expected == _CORPUS_MAP


# --- bulk_inventory.jurisdiction_from_filename -------------------------------


@pytest.mark.parametrize("j", _ALL)
def test_bulk_inventory_jurisdiction_from_filename(j):
    assert jurisdiction_from_filename(f"{j.stem}.txt") == j.code


def test_bulk_inventory_unknown_stem_falls_back_to_upper():
    assert jurisdiction_from_filename("Unknown_Law.txt") == "UNKNOWN_LAW"


# --- generate_lbo_inventory._STATE_CONFIGS -----------------------------------


def test_generate_lbo_inventory_configs_are_derived():
    expected = {
        j.stem: {
            "full_name": j.full_name,
            "jurisdiction": j.code,
            "source_suffix": j.stem,
            "header_type": j.header_type,
        }
        for j in JURISDICTIONS
        if j.header_type is not None
    }
    assert expected == _STATE_CONFIGS
    assert len(_STATE_CONFIGS) == 13


# --- bulk_extract.PDFS -------------------------------------------------------


def test_bulk_extract_pdfs_are_derived():
    assert PDFS == [f"{j.stem}.pdf" for j in JURISDICTIONS if j.extract_from_pdf]
    assert all((_RAW_DIR / name).is_file() for name in PDFS)


def test_bulk_extract_writes_txt_files_the_registry_knows():
    """bulk_extract names each txt after its PDF; that stem must be a registry stem."""
    for name in PDFS:
        by_stem(Path(name).stem)


# --- audit_extraction_artifacts.py -------------------------------------------


def test_audit_discovers_exactly_the_16_states():
    assert discover_states() == sorted(j.stem for j in STATES)


@pytest.mark.parametrize("j", _STATE_PARAMS)
def test_audit_resolves_the_corpus_file(j):
    txt_name = _TXT_PATH_OVERRIDES.get(j.stem, f"{j.stem}.txt")
    assert Path(txt_name).stem == j.stem, f"{j.label}: audit override points to '{txt_name}'"
    assert (_TXT_DIR / txt_name).is_file()


# --- further consumers found in the PR #7 review ------------------------------


def test_graph_spot_check_expected_states_are_derived():
    assert sorted(EXPECTED_STATES) == sorted(j.stem for j in STATES)


@pytest.mark.parametrize("j", _ALL)
def test_draft_inventory_law_name(j):
    assert _full_lbo_name(j.stem) == j.full_name


def test_situation_german_states_are_derived():
    assert sorted(j.label for j in STATES) == GERMAN_STATES


# --- hand-written per-state lists: keys must be registry stems ---------------


def test_kg_audit_anchor_keys_are_registry_stems():
    """Thresholds per law; BW_LBO and BremLBO have none yet (see F010)."""
    assert set(_EXPECTED_ANCHORS) <= {j.stem for j in STATES}


def test_fix_flat_inventories_states_are_registry_stems():
    assert set(FIX_FLAT_STATES) <= {j.stem for j in STATES}
