# Adding a new state LBO to the knowledge graph

This guide is for adding another state’s building code (e.g. BayBO, NBauO) to the Propra graph, so the same pipeline and relationship structure as Brandenburg (BbgBO) can be reused.

**Reference implementation:** BbgBO (Brandenburg). Use it as the template for file names, registry shape, and mapping.

---

## What you get

- A **state root node** (e.g. `BayBO_ROOT`) as the central node for that law.
- **Section anchors** (e.g. `BayBO_§1`, `BayBO_§6`) and **content nodes** at sentence/list-item granularity.
- **Structural edges** (`sub_item_of`, `supplements`) plus **edges copied from MBO** (e.g. `exception_of`, `references`) where the section mapping exists.
- The product **cites only the LBO** (e.g. “§ 6 BayBO”); MBO is used only internally for structure and mapping.

---

## Prerequisites

- **Paragraph-level node inventory** for the state in `propra/data/node inventory/`  
  Format: `### § N — Title`, `**type:**`, `**source_paragraph:**`, table `| Nr. | Regeltext |` with one row per Absatz (e.g. `6.1`, `6.2`).  
  If you don’t have one: PDF → `extract_pdf_clean.py` → `data/txt/*.txt` → `draft_inventory.py` → review and commit. See `propra/graph/node_inventory_guide.md`.
- **Python** 3.11+, deps from repo root: `pip install -r requirements.txt`.

---

## Steps (overview)

| Step | What | Where / command |
|------|------|------------------|
| 1 | Refine inventory to sentence/list-item level (match MBO granularity) | `split_inventory_to_sentences.py` |
| 2 | Create BbgBO↔MBO section mapping (if you want MBO edges copied) | `map_to_mbo.py` → `data/{STATE}_mbo_mapping.json` |
| 3 | Register the state in the single registry | `propra/jurisdictions.py` → `JURISDICTIONS` |
| 4 | Optionally generate a Brandenburg-style reviewable section-edge module | `generate_state_section_edges.py` |
| 5 | Build and check | `python -m propra.graph.build_graph` |

---

## Step 1 — Refine granularity

The graph expects **sentence/list-item** row IDs (e.g. `1.1`, `1.2`, `2.1` under §6), not one row per paragraph. Use the split script:

```bash
cd /path/to/proplaw
python -m propra.data.split_inventory_to_sentences \
  --input "propra/data/node inventory/BayBO_node_inventory.md" \
  --output "propra/data/node inventory/BayBO_node_inventory_fine.md"
# Or: python propra/data/split_inventory_to_sentences.py --input "..." --output "..."
```

- **Input:** Your paragraph-level inventory (e.g. from `draft_inventory.py` or an existing `*_node_inventory.md`).
- **Output:** New file `*_node_inventory_fine.md` with the same section blocks and table format, but more rows and `Nr.` like `1.1`, `1.2`, `2.1` (Absatz.Satz).
- Inspect a few sections (e.g. §1, §6) in the fine file; fix any over-splits (e.g. at “Abs.”, “Nr.”) by editing the script or the markdown.

---

## Step 2 — Create section mapping (optional but recommended)

The mapping links state § to MBO § so we can copy MBO relationship edges (e.g. `exception_of`, `sub_item_of`) onto your state.

```bash
python -m propra.graph.map_to_mbo --state BayBO
```

- Reads `propra/data/node inventory/BayBO_node_inventory_fine.md` (or `BayBO_node_inventory_v2.md` if no `_fine`).
- Writes `propra/data/BayBO_mbo_mapping.json` with `mapping: { "state_§": "mbo_§", ... }` and a `review` list for low-confidence matches.
- **Edit the JSON** if needed: move entries between `mapping` and `review`, or fix wrong MBO §. The build only uses the `mapping` object.

---

## Step 3 — Register the state

Add one entry to `JURISDICTIONS` in `propra/jurisdictions.py`. It is the single
source of truth for which corpus file belongs to which state (F010); the graph
build, retrieval, benchmark judge and data scripts all derive from it.

```python
Jurisdiction(
    "BayBO",                           # stem: file name of raw PDF, txt and inventory; KG prefix "BayBO_"
    "DE-BY",                           # ISO 3166-2 code
    "Bayern",                          # German label
    "Bayerische Bauordnung (BayBO)",   # law name shown to users (see F014)
),
```

- The **stem** names every file of the state: `data/raw/{stem}.pdf`,
  `data/txt/{stem}.txt`, `data/node inventory/{stem}_node_inventory_fine.md`,
  and the mapping file `data/{stem}_mbo_mapping.json`.
- Node IDs use the prefix `{stem}_` (e.g. `BayBO_§6_1.1`, `BayBO_ROOT`).
- Run `PYTHONPATH=. pytest propra/tests/test_prefix_alignment.py`. It fails if a
  file is missing or misnamed.

No other code changes are required for the baseline graph: the build loads the inventory, creates section anchors and structural edges, and copies MBO edges when the mapping file contains confirmed matches.

If you want a Brandenburg-style reviewed layer, generate a draft section-edge module and then edit it by hand:

```bash
python -m propra.graph.generate_state_section_edges --state BayBO
```

- Default output: `propra/graph/baybo_section_edges.py`
- The build automatically uses `propra.graph.{state_lower}_section_edges` when that module exists.
- This is the recommended path once a state is important enough to curate beyond structural edges + raw mapping.

---

## Step 4 — Build and verify

```bash
python -m propra.graph.build_graph
```

Check the log:

- “Parsed N nodes from …_fine.md” for your state.
- “{State} section anchors: M” and “{State} structural (sub_item_of): K edges”.
- “{State} from MBO (mapping): L edges” if the mapping file was found.
- Or “{State} section (curated structural + domain): L edges” when a reviewed section-edge module exists.

Then e.g.:

- Open `propra/data/graph.html` (from `python -m propra.graph.visualize_html`) and filter by your state prefix.
- Confirm the state root exists: e.g. `BayBO_ROOT` (central node for that law).

---

## File checklist

| Item | Location |
|------|----------|
| Paragraph-level inventory (draft) | `propra/data/node inventory/{STATE}_node_inventory.md` |
| Fine-grained inventory | `propra/data/node inventory/{STATE}_node_inventory_fine.md` |
| Section mapping (optional) | `propra/data/{STATE}_mbo_mapping.json` |
| Registry entry | `propra/jurisdictions.py` → `JURISDICTIONS` |

---

## Using Cursor or Claude

You can do this entirely with an AI assistant:

1. **“Add [state] LBO to the knowledge graph”** — point to this doc and the BbgBO entry in `propra/jurisdictions.py` and the files under `propra/data/node inventory/` and `propra/data/BbgBO_mbo_mapping.json`.
2. **“Refine the inventory for [state] to sentence level”** — run `split_inventory_to_sentences.py` with the right `--input` and `--output` for that state.
3. **“Create the MBO mapping for [state]”** — run `map_to_mbo --state …`, then review/edit the generated JSON.
4. **“Register [state]”** — add one `Jurisdiction` entry to `propra/jurisdictions.py` and run `propra/tests/test_prefix_alignment.py`.

The **central node** for the state is always `{prefix}ROOT` (e.g. `BbgBO_ROOT`, `BayBO_ROOT`). All section anchors link to it via `supplements`.
