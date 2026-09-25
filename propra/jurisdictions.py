"""Single source of truth: which corpus file belongs to which jurisdiction (F010).

Every building code in the corpus has exactly one entry here. All other modules
derive their mappings from this registry instead of keeping their own tables:

- ``propra.retrieval.rag.JURISDICTION_MAP``            stem -> ISO code, label
- ``propra.graph.build_graph._STATE_REGISTRY``         KG build config per state
- ``propra.benchmark.judge_runner._CORPUS_MAP``        ISO code / label -> stem
- ``propra.data.bulk_inventory.jurisdiction_from_filename``
- ``propra.data.generate_lbo_inventory._STATE_CONFIGS`` parser config per state
- ``propra.data.bulk_extract.PDFS``                    PDFs to extract
- ``propra.eval.graph_spot_check.EXPECTED_STATES``    stems expected in the KG
- ``propra.data.draft_inventory._full_lbo_name``      stem -> law name
- ``propra.schemas.situation.GERMAN_STATES``          state labels for input validation

The ``stem`` is the shared file name for one building code across the data
directories: ``data/raw/<stem>.pdf``, ``data/txt/<stem>.txt`` and
``data/node inventory/<stem>_node_inventory_fine.md``. The KG node prefix is
``<stem>_``; GraphRAG derives node IDs from the FAISS ``source_file`` (the
stem), so the two must never diverge. ``propra/tests/test_prefix_alignment.py``
enforces this.

To add a state: add one ``Jurisdiction`` entry, drop the files named after its
stem into the data directories, and run the tests.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Jurisdiction:
    """One building code in the corpus."""

    stem: str
    """File stem shared by raw PDF, txt, node inventory and KG prefix."""

    code: str
    """ISO 3166-2 code, e.g. ``DE-BB``. The MBO uses the pseudo code ``DE-MBO``."""

    label: str
    """German name of the jurisdiction, e.g. ``Brandenburg``."""

    full_name: str
    """Name of the law as shown to users. Official wording unverified, see F014."""

    header_type: str | None = None
    """Section header format for ``generate_lbo_inventory.py``; ``None`` if that
    script does not handle this code (see the comments on each value there)."""

    extract_from_pdf: bool = True
    """Whether ``bulk_extract.py`` builds the txt file from the raw PDF."""

    @property
    def is_state(self) -> bool:
        """True for the 16 Bundesländer, False for the MBO."""
        return self.code != "DE-MBO"


# Order matters: it is the order in which build_graph adds the states to the KG.
JURISDICTIONS: tuple[Jurisdiction, ...] = (
    Jurisdiction("BbgBO", "DE-BB", "Brandenburg", "Brandenburgische Bauordnung (BbgBO)"),
    Jurisdiction("BayBO", "DE-BY", "Bayern", "Bayerische Bauordnung (BayBO)"),
    Jurisdiction("NBauO", "DE-NI", "Niedersachsen", "Niedersächsische Bauordnung (NBauO)"),
    # After trimming the repeated ToC, the actual law body parses as no_dash.
    Jurisdiction("BauO_BE", "DE-BE", "Berlin", "Bauordnung für Berlin (BauO BE)", "no_dash"),
    # After dropping the repeated ToC block, the real law body parses as no_dash.
    Jurisdiction("BauO_HE", "DE-HE", "Hessen", "Hessische Bauordnung (HBO)", "no_dash"),
    Jurisdiction("BauO_NRW", "DE-NW", "Nordrhein-Westfalen", "Bauordnung für das Land Nordrhein-Westfalen (BauO NRW)", "no_dash"),
    Jurisdiction("BauO_LSA", "DE-ST", "Sachsen-Anhalt", "Bauordnung des Landes Sachsen-Anhalt (BauO LSA)", "no_dash"),
    Jurisdiction("BauO_MV", "DE-MV", "Mecklenburg-Vorpommern", "Landesbauordnung Mecklenburg-Vorpommern (LBauO M-V)", "no_dash"),
    # Official PDF-backed text parses as no_dash after trimming preamble/annex.
    Jurisdiction("HBauO", "DE-HH", "Hamburg", "Hamburgische Bauordnung (HBauO)", "no_dash"),
    Jurisdiction("LBO_SH", "DE-SH", "Schleswig-Holstein", "Landesbauordnung Schleswig-Holstein (LBO)", "no_dash"),
    Jurisdiction("LBO_SL", "DE-SL", "Saarland", "Landesbauordnung Saarland (LBO)", "no_dash"),
    Jurisdiction("LBauO_RLP", "DE-RP", "Rheinland-Pfalz", "Landesbauordnung Rheinland-Pfalz (LBauO RLP)", "no_dash"),
    Jurisdiction("SaechsBO", "DE-SN", "Sachsen", "Sächsische Bauordnung (SächsBO)", "no_dash"),
    Jurisdiction("ThuerBO", "DE-TH", "Thüringen", "Thüringer Bauordnung (ThürBO)", "no_dash"),
    Jurisdiction("BW_LBO", "DE-BW", "Baden-Württemberg", "Landesbauordnung für Baden-Württemberg (LBO BW)", "from_flat", extract_from_pdf=False),
    Jurisdiction("BremLBO", "DE-HB", "Bremen", "Bremische Landesbauordnung (BremLBO)", "from_flat"),
    Jurisdiction("MBO", "DE-MBO", "Musterbauordnung", "Musterbauordnung (MBO)", extract_from_pdf=False),
)

STATES: tuple[Jurisdiction, ...] = tuple(j for j in JURISDICTIONS if j.is_state)

_BY_STEM = {j.stem: j for j in JURISDICTIONS}
_BY_CODE = {j.code: j for j in JURISDICTIONS}
_BY_LABEL = {j.label: j for j in JURISDICTIONS}


def by_stem(stem: str) -> Jurisdiction:
    """Look up by file stem, e.g. ``BremLBO``. Raises KeyError if unknown."""
    return _BY_STEM[stem]


def by_code(code: str) -> Jurisdiction:
    """Look up by ISO 3166-2 code, e.g. ``DE-HB``. Raises KeyError if unknown."""
    return _BY_CODE[code]


def by_label(label: str) -> Jurisdiction:
    """Look up by German label, e.g. ``Bremen``. Raises KeyError if unknown."""
    return _BY_LABEL[label]
