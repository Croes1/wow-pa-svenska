# translation/PIPELINE.md — the loop for newly collected data (agent edition)

This file is the **standard procedure** whenever new English data arrives
(collected in-game by the Collector, or extracted from WDB files). It is
written to be re-run any number of times — by a human *or* the AI agent
working in the VS Code chat. Do the steps in order; every step has a check
that **must** be green before the next one starts.

## HARD RULE — the agent never calls a translation API

**Any AI is not allowed: no AI services, no translation APIs, no LLM/model
endpoints, no HTTP calls of any kind.**
The agent in the VS Code chat **is** the translator: it reads the TASK blocks
in `translation/PROMPT-GEMMA.md`, does the segmentation (TASK A) and the
Swedish translation (TASK B) itself, and writes the results directly to the
TSV files. The only programs allowed in this loop are the offline,
network-free tools in `tools/` (see the inventory below). The old API runner
(`tools/run-gemma.py`), its tests, the API key (`.env`) and the /tmp queue
scripts were removed on 2026-11-15 — do not restore them or any equivalent.

The short flow:

```
collector/WDB  →  cache TSV  →  select-untranslated  →  make-batches
    →  per batch: [agent segments → verify → review → agent translates → validate]
    →  human quality pass  →  READY FOR MERGE
```

Merge (`Data/QuestExtra.lua` + `Data/NpcExtra.lua`) is a **separate,
separately reviewed task** — this loop stops at "ready for merge".

## How new data arrives in this repo

The enUS client does the collecting by itself: while playing it writes
`Cache/WDB/questcache.wdb` and `Cache/WDB/creaturecache.wdb` (no addon
needed). The maintainer quits the game, copies those two files into the repo
and converts them with `python3 tools/parse-wdb.py <cache.wdb> <out.tsv>`
into the TAB-separated caches in `translation/`:

- `translation/questcache-en.tsv`  (`id<TAB>text` — quests glued into one
  line: title+objectives+description+progress+reward)
- `translation/creaturecache-en.tsv` (`id<TAB>name<TAB>title`)

Player feedback comes in as `/wps fel` reports (`WPSDB.reports`, see below),
and item/spell/zone/UI data comes as maintainer exports from wago.tools /
cmangos — those are `Data/` edits, never part of an agent round. (A
voluntary in-game Collector addon is planned but does not exist yet; if it
appears, its SavedVariables dump is raw input only.)

## What to tell the agent when new data has been saved

One sentence is enough:

> "Ny data är sparad i translation/questcache-en.tsv (+ creaturecache-en.tsv).
> Läs AGENTS.md och translation/PIPELINE.md och kör nästa översättningsrunda."

The agent then: (1) reads `AGENTS.md` → this file → the TASK/style files,
(2) checks the caches, (3) runs Loop Point 1, (4) works the batches at
Loop Point 2/3, (5) stops before merge and reports what is ready for review.

## Before ANY translation — the pre-flight checklist

1. Read the entry chain: `AGENTS.md`, this file,
   `translation/PROMPT-GEMMA.md`, `translation/PROMPT-translation.md`, plus
   the latest `translation/batches/review/DECISIONS-*.md` for placement and
   terminology precedent.
2. Cache sanity: files exist, UTF-8, TAB-separated; quest cache = 2 columns,
   creature cache = 3; eyeball a few rows; `wc -l` both files.
3. Test suite once per round: `python3 -m unittest discover -s tests` →
   must end with `OK` (run it when tools changed, or when in doubt).
4. Directories exist: `translation/segmented`, `translation/out`,
   `translation/batches/review`.

## Loop Point 1 — new data arrives (per delivery round)

1. **Select everything missing** (compares the caches against
   `Data/Quest.lua` + `Data/Npc.lua`):
   `python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv>`
   - Rewrites `translation/quest-not-translated.tsv` (`id<TAB>text`) and
     `translation/npcs-not-translated.tsv` (`id<TAB>name<TAB>title`).
   - Keep the console output: `overlapp > 0` confirms the id semantics line
     up between caches and shipped data.
2. **Regenerate batches** (10 quests / 150 NPCs per file):
   `python3 tools/make-batches.py`
   - Recreates `translation/batches/quests-batch-XX.tsv` and
     `translation/batches/npcs-batch-XX.tsv`. Check with
     `wc -l translation/batches/*.tsv`.
3. **Stale rule.** If the not-yet-translated set changed since the last
   round:
   - Preferred order: *finish* all batches of the running round (and archive
     `translation/out/`) **before** pulling new data.
   - If you must mix: archive `translation/segmented/`, `translation/out/`
     and the review files (keep the DECISIONS notes!), then restart from
     Loop Point 2 for the whole round. Mixing old output with renumbered
     batches risks mismatched pairs.

## Loop Point 2 — per quest batch (XX = 01, 02, … N)

The agent does both steps itself, following the TASK blocks in
`translation/PROMPT-GEMMA.md` verbatim and the style rules in
`translation/PROMPT-translation.md` (glossary first).

1. **Segment** (TASK A — exact partition, no translation):
   - Write `translation/segmented/quests-batch-XX-en-segmented.tsv`:
     `id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward`.
     Six columns on every row; a field that does not exist stays EMPTY; game
     tokens stay attached byte for byte; same ids, same order as the source
     batch.
   - Check: `python3 tools/verify-segmentation.py translation/batches/quests-batch-XX.tsv translation/segmented/quests-batch-XX-en-segmented.tsv`
     → `RESULTAT: OK` required (exit 0). The check proves the five fields
     concatenated equal the source text (modulo end-of-row whitespace). It
     can NOT prove the text landed in the RIGHT field — that is what the
     review below is for.
   - A row that fails the partition: re-do that row yourself, never by
     inventing text to force a fit. Keep impossible rows routed to review
     instead; two rounds without progress → hand those ids to the human
     (never to an API).
2. **Review the routed rows** (if a review file was created):
   `translation/batches/review/quests-batch-XX-en-review.tsv`.
   - Every routed row (empty title / fragments like `93429`, `< ... >`, or a
     starting-lowercase/`$`-token body) needs a field-placement decision —
     the source record is incomplete; never invent the missing parts.
   - **Record the decision** in
     `translation/batches/review/DECISIONS-YYYY-MM-DD.md` (the checker
     rewrites the review files on every run, so the notes live in a separate
     decisions file).
   - Placement corrections go into the *segmented* file; then re-run the
     verify — it must still report `RESULTAT: OK`.
3. **Translate** (TASK B — Swedish; glossary from
   `translation/glossary-core.tsv`, deeper lookups in
   `translation/glossary-all.tsv`):
   - Write `translation/out/quests-batch-XX-sv.tsv`: same six columns, same
     ids and order; empty stays empty; tokens byte for byte.
   - Check: `python3 tools/validate-batch.py translation/batches/quests-batch-XX.tsv translation/out/quests-batch-XX-sv.tsv quests`
     → `RESULTAT: OK (n varningar)` required (exit 0). The validator compares
     token multisets (`$B/$b/$n/$c/$r/$C/$2oa/#/#/%s` …) row by row.
   - Normal warnings: `titeln ar tom` (review rows with no title) and
     `oforandrad engelska` (a field still holds English — eyeball that row).
   - `kolumner (vantade 6)` = dropped trailing empty columns: run
     `python3 tools/fix-empty-columns.py <segmented> <out>` and re-validate.
4. **Human quality pass** — the tools cannot judge Swedish (the agent may
   prepare it; the human signs it off):
   - leftover-English hint:
     `grep -nE "\b(the|those|and|with|Old)\b" translation/out/quests-batch-XX-sv.tsv`
     (hint only; English proper names may be intentionally kept).
   - glossary spellings: Understaden, Tirisfalgläntorna, Skurk / Skurkarnas
     kvarter, Järnsmedjan, Mörkby, Stormvind, Elwynnskogen, Kargmarkerna …
   - punctuation around `$B`/`$b`, capitals and final periods, the " ..."
     ellipsis pattern, straight quotation marks.

## Loop Point 3 — per NPC batch

Same pattern as step 3 above, but: source is
`translation/batches/npcs-batch-XX.tsv` (`id<TAB>name<TAB>title`), output
`translation/out/npcs-batch-XX-sv.tsv` (`id<TAB>swedish-name`, 2 columns),
validated with `... npcs` instead of `quests`.

- The source `title` column is reference only; it must not appear in the
  output.
- The `namnet oforandrat` warning is *intended* for personal names (Karu,
  Demnul Farmountain …). At the same time check that **descriptive** names
  (Goblin Shipbuilder, Timber Wolf …) really were translated, and that a rank
  prefix was translated only (Deputy Feldon → Konstapel Feldon).
- `mellanslag kring namnet`: fix in the file.
- Glossary: Rogue = Skurk (player class / villain person / district / mob
  names); shipped-data exceptions: "scalawag" = skälm and the harpy
  "Roguefeather" = Blodvredesskälmfjäder.

## Round acceptance (before "ready for merge")

- All `translation/segmented/*.tsv` passed verify (`RESULTAT: OK`).
- All `translation/out/*.tsv` passed validate (`RESULTAT: OK`).
- All routed review rows have a recorded placement decision (DECISIONS file).
- The quality pass (step 4 in every batch) is done.
- The numbers line up: `wc -l` of every out file matches its batch file, and
  the id order matches the batch order.

## Offline tools inventory (everything that may be run — all network-free)

| tool | what it does |
|---|---|
| `tools/parse-wdb.py` | client WDB cache → TSV |
| `tools/select-untranslated.py` | caches − shipped data = work lists |
| `tools/make-batches.py` | work lists → batches (10 quests / 150 NPCs per file) |
| `tools/verify-segmentation.py` | step A check (exact partition) + review routing |
| `tools/validate-batch.py` | step B check (ids, columns, token multisets) |
| `tools/fix-empty-columns.py` | restore dropped empty trailing columns |
| `tools/export-glossary.lua` | in-game glossary export (source of the glossary TSVs) |

`tools/run-gemma.py` and its test **were removed** (they drove a translation
model API). If you ever feel the urge to call a model endpoint — don't; any
AI is not allowed. Translate yourself in the chat and let the checkers judge
the result.

## Failure catalogue

| Symptom | Cause | Fix |
|---|---|---|
| `sammanfogningen stammer inte` | segments invented/lost text | re-do that row (TASK A); NEVER patch with invented text |
| `platshallare saknas/tillagda` | tokens dropped/added/altered | retranslate that row; count `$B/$b` pairs against the source |
| `kolumner (vantade 6)` | trailing empty columns dropped | `fix-empty-columns.py`, then re-validate |
| id-saknas/dubbletter/ordning | rows added in wrong order or lost | rebuild the file in source batch order |
| terminal mangles commands | VS Code shell-integration quirk | write a small script to /tmp, run it with output redirected to a file, then Read the file |
| `FEL: kan inte lasa` | path/encoding problem | check the file exists and is UTF-8 |

## Tool messages (Swedish → meaning)

| message | meaning |
|---|---|
| `RESULTAT: OK` | checks passed (warnings may follow) |
| `FEL:` | error — the item is not accepted, exit code 1 |
| `VARNING:` | warning — accepted, but eyeball it |
| `indata/utdata/jamforda: N rader` | rows read in source / output / actually compared |
| `titeln ar tom` | the title field is empty (normal for fragment records) |
| `namnet oforandrat` | NPC name unchanged (correct for personal names) |
| `mellanslag kring namnet` | whitespace around the name — fix |
| `oforandrad engelska` | a field still holds the English text — eyeball |
| `sammanfogningen stammer inte` | segmented fields do not rebuild the source — reject |
| `kan inte lasa` | cannot read the file (path/encoding problem) |

## Rules (invariants for both humans and AI)

- **No translation APIs. Ever.** The agent translates itself in the chat
  session; no AI service of any brand is allowed in this repo.
- **Never invent text.** Segmentation is an exact partition; translation is
  translation; uncertainty → leave the field empty/English and route the row
  to review.
- Missing `l` objective lines are a data-flow coverage limitation — never
  invent them.
- **Never touch `Data/*.lua`** in this loop (generated files; all existing
  translations must be preserved).
- Exit codes rule: 0 = done, 1 = ERROR (incl. failed ids), 2 = bad
  invocation. Continue only on 0 — or when an ERROR print shows exactly
  which ids to retry.
- Green checkers do NOT prove the Swedish is good: the quality sources remain
  human review and `/wps fel` reports from in-game.

## Loop Point 4 — STOP: merge is out of scope

When acceptance is green, hand over `translation/out/*.tsv` (the Swedish
files) plus the review/DECISIONS notes to the merge step — a separate,
separately reviewed task. The merge does NOT touch the generated
`Data/Quest.lua` / `Data/Npc.lua`: it creates additive
`Data/QuestExtra.lua` / `Data/NpcExtra.lua` (`local extra = {...}` +
nil-guarded merge loop, jfr `Data/UiExtra.lua`), regeneratable and
idempotent, and links them in `.toc` after their main files. Tool:
`python3 tools/merge-translation.py` (offline; also marks rows already in
the main Data files as skipped). *(Done for the 2026-11-15 round.)* This
loop restarts at Loop Point 1 the next time new data arrives.

## Quick reference (the whole loop for one round)

```
python3 -m unittest discover -s tests                # once per round
wc -l translation/questcache-en.tsv translation/creaturecache-en.tsv
python3 tools/select-untranslated.py translation/questcache-en.tsv \
        translation/creaturecache-en.tsv
python3 tools/make-batches.py
# per quests-batch XX — the agent does both steps itself in the chat:
#   TASK A -> translation/segmented/quests-batch-XX-en-segmented.tsv
python3 tools/verify-segmentation.py \
    translation/batches/quests-batch-XX.tsv \
    translation/segmented/quests-batch-XX-en-segmented.tsv
#   TASK B -> translation/out/quests-batch-XX-sv.tsv
python3 tools/validate-batch.py translation/batches/quests-batch-XX.tsv \
    translation/out/quests-batch-XX-sv.tsv quests
# per npcs-batch XX:
#   TASK B/NPC -> translation/out/npcs-batch-XX-sv.tsv
python3 tools/validate-batch.py translation/batches/npcs-batch-XX.tsv \
    translation/out/npcs-batch-XX-sv.tsv npcs
# STOP -> hand translation/out/ + review DECISIONS to the merge step
```