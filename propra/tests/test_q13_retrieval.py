"""Check that FAISS retrieval for benchmark Q13 reaches § 61 BbgBO (F004).

Q13 asks "Wann ist ein Bauvorhaben verfahrensfrei?". In Brandenburg the answer
is § 61 BbgBO, titled "Genehmigungsfreie Vorhaben". The corpus contains the
full section (propra/data/txt/BbgBO.txt), yet on 2026-09-26 none of the top 8
DE-BB hits came from § 61. The same query with "genehmigungsfrei" ranks
§ 61 sixth. The gap is the query term, not the corpus.

The test is marked xfail(strict=True): it documents the defect today, and it
turns red as soon as retrieval reaches § 61, so the marker has to be removed
together with the fix. ``raises=AssertionError`` keeps other failures (a
missing model, a network error) from passing as the known defect.

The FAISS index is a local build artefact and not in the repo, so the test is
skipped where it does not exist (CI). Where it exists, the embedding model was
downloaded to build it, so the test loads the model from the local cache in
Hugging Face offline mode. Online, every model load first sends HEAD requests
to huggingface.co, which fail SSL verification on the development machine
(same cause as F016).
"""

import huggingface_hub.constants
import pytest

from propra.retrieval.rag import CHUNKS_PATH, INDEX_PATH, Retriever

Q13 = "Wann ist ein Bauvorhaben verfahrensfrei?"


@pytest.mark.skipif(
    not (INDEX_PATH.exists() and CHUNKS_PATH.exists()),
    reason="FAISS index not built (python -m propra.retrieval.rag build)",
)
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="F004: query term 'verfahrensfrei' vs BbgBO 'Genehmigungsfreie Vorhaben'",
)
def test_q13_retrieval_reaches_bbgbo_section_61(monkeypatch):
    monkeypatch.setattr(huggingface_hub.constants, "HF_HUB_OFFLINE", True)
    hits = Retriever().retrieve(Q13, k=8, jurisdiction="DE-BB")
    paragraphs = [h["source_paragraph"] for h in hits]
    assert any(p.startswith("§ 61 ") for p in paragraphs), paragraphs
