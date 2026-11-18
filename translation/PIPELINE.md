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
  →  per batch: [agent segments where needed → verify → translate → validate]
    →  human quality pass  →  READY FOR MERGE
```

Merge (`Data/QuestExtra.lua` + `Data/NpcExtra.lua`) is a **separate,
separately reviewed task** — this loop stops at "ready for merge".

## How new data arrives in this repo

The enUS client does the collecting by itself: while playing it writes
`Cache/WDB/questcache.wdb`, `creaturecache.wdb`, `gameobjectcache.wdb` and
`pagetextcache.wdb` (no addon needed). The maintainer quits the game, copies
those files into the repo and converts them with
`python3 tools/parse-wdb.py <cache.wdb> tsv <out.tsv>` into the tab-separated
caches in `translation/`:

- `translation/questcache-en.tsv`  (`id<TAB>text` — quests glued into one
  line: title+objectives+description+progress+reward)
- `translation/creaturecache-en.tsv` (`id<TAB>name<TAB>title`)
- `translation/gameobjectcache-en.tsv` (`id<TAB>name<TAB>extra`)
- `translation/pagetextcache-en.tsv` (`id<TAB>text`)

`npccache.wdb` and `petitioncache.wdb` are also recognized. The current
client files are header-only, so they do not produce translation work.

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

1. **Select everything missing** (the first two inputs compare against
  `Data/Quest.lua` + `Data/Npc.lua`; optional game-object and page-text inputs
  have no shipped translation tables yet, so all their rows are selected):
   `python3 tools/select-untranslated.py <quest-en.tsv> <creature-en.tsv>`
   - Writes a new numbered file per kind to `translation/untranslated/`:
     `quests-NNN.tsv` (`id<TAB>text`) and `npcs-NNN.tsv`
     (`id<TAB>name<TAB>title`). Existing files are never changed; a run only
     adds rows not already in an earlier file, and writes nothing if there are none.
   - Keep the console output: `overlapp > 0` confirms the id semantics line
     up between caches and shipped data.
   - To include the optional types, append `<gameobject-en.tsv> <pagetext-en.tsv>`.
     This writes `gameobjects-NNN.tsv` and `pagetext-NNN.tsv` the same way.
2. **Regenerate batches** (10 quests / 150 NPCs and page texts / 150 game
   objects per file when those optional worklists exist):
   `python3 tools/make-batches.py`
   - Reads all numbered files in `translation/untranslated/` (in number order)
     and recreates `translation/batches/quests-batch-XX.tsv` and
     `translation/batches/npcs-batch-XX.tsv`. Check with
     `wc -l translation/batches/*.tsv`.
3. **Ids already in the Extra files.** `select-untranslated.py` compares only
   against `Data/Quest.lua` and `Data/Npc.lua`, so ids that are already in
   `Data/QuestExtra.lua` / `Data/NpcExtra.lua` show up in the batches again
   (round 2026-11-18: 79 quests, 1,136 NPCs). Before translating, list them
   and decide per id:
   - **Complete row in the Extra file** (title, objectives and description
     present, and it validates against the source): reuse that text unchanged.
   - **Fragment row** (only some fields): translate the whole row and record it
     in the DECISIONS file; the merge replaces the fragment.
   - Never overwrite a reviewed shipped text with new wording unless a human
     asked for it; note every such case in the DECISIONS file.
4. **Stale rule.** If the not-yet-translated set changed since the last
   round:
   - Preferred order: *finish* all batches of the running round (and archive
     `translation/out/`) **before** pulling new data.
   - If you must mix: archive `translation/segmented/`, `translation/out/`
     and the review files (keep the DECISIONS notes!), then restart from
     Loop Point 2 for the whole round. Mixing old output with renumbered
     batches risks mismatched pairs.
   - **Archive before regenerating** (this keeps the old pairs intact):
     `mkdir -p translation/archive/YYYY-MM-DD && cp -r translation/out translation/segmented translation/batches translation/archive/YYYY-MM-DD/`
   - **Never copy old output back into `translation/out/`.** The merge aborts if
     one id occurs in two out files. Restore single files from git
     (`git show <tag>:translation/out/<file>`), not from a backup folder.

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

## Optional game-object and page-text batches

These are batchable, but are not part of `tools/merge-translation.py` and do
not currently appear translated in-game.

- Game objects: source `gameobjects-batch-XX.tsv` is `id<TAB>name<TAB>title`;
  output `translation/out/gameobjects-batch-XX-sv.tsv` as
  `id<TAB>Swedish name`. The title is reference only. Validate with
  `... gameobjects`.
  **Known blocker:** game-object entry ids repeat by design in the cache
  (round 2026-11-18: 952 rows, 598 unique ids), so `validate-batch.py` always
  reports `FEL: kalla: id N forekommer flere ganger` for these batches. The
  rows in `out/` are in source order and otherwise consistent, but id → name
  is ambiguous, so they must not be merged. Fixing this needs a different key
  (for example id + name) in the tools and in any runtime table, as a separate
  reviewed change. The 2026-11-18 game-object batches were left out of the
  commit for this reason.
- Page text: source `pagetext-batch-XX.tsv` is `id<TAB>text`; translate the
  whole page as one field to `translation/out/pagetext-batch-XX-sv.tsv`, also
  `id<TAB>text`. Do not segment it. Validate with `... pagetext`.
- Preserve IDs, row order, placeholders and literal escaped line breaks.
  Their future runtime integration and merge destination require a separate
  reviewed change.

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
| `tools/make-batches.py` | work lists → batches (10 quests/page texts, 150 NPCs/game objects per file) |
| `tools/verify-segmentation.py` | step A check (exact partition) + review routing |
| `tools/validate-batch.py` | batch check (ids, columns, token multisets; quests, NPCs, game objects, page text) |
| `tools/fix-empty-columns.py` | restore dropped empty trailing columns |
| `tools/export-glossary.lua` | in-game glossary export (source of the glossary TSVs) |
| `tools/combine-wdb.py` | combine several WDB folders into the cache TSVs (game-object rows deduplicated only when exactly equal) |
| `tools/merge-translation.py` | `translation/out/` → `Data/QuestExtra.lua` / `Data/NpcExtra.lua` (see Loop Point 4; use `--torr` first) |
| `tools/parse-uidump.py` | `/wps dump` SavedVariables → English UI list |
| `tools/check-ui-translation.lua` | checks a UI en/sv pair against `Data/Ui.lua` + `Data/UiExtra.lua` |

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
| `FEL: kalla: id N forekommer flere ganger` (game objects) | entry ids repeat by design in the cache | not fixable in the batch; see "Optional game-object and page-text batches" |
| `id N forekommer i bade X och Y` (merge) | the same id is in two out files | remove the duplicate; never restore old out files next to new ones |
| ids missing from the Extra file after a merge | merge regenerates the Extra files from `out/` only | keep a carry-over out file with those rows, then diff old vs new Extra files |

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
nil-guarded merge loop, jfr `Data/UiExtra.lua`) and links them in `.toc`
after their main files. Tool: `python3 tools/merge-translation.py`
(offline). *(Done for the 2026-11-15 and 2026-11-18 rounds.)* This loop
restarts at Loop Point 1 the next time new data arrives.

How the merge really behaves (read this before running it):

- It **regenerates both Extra files completely from `translation/out/`** on
  every run. It only skips ids that are in `Data/Quest.lua` / `Data/Npc.lua`;
  it does **not** skip ids already in the Extra files.
- Therefore every id that is in a shipped Extra file must also be in some
  `translation/out/` file, or the merge **drops it**. When old out files are no
  longer in `out/`, extract the missing rows from the current Extra files into
  carry-over files (for 2026-11-18: `quests-batch-32-sv.tsv`,
  `npcs-batch-27-sv.tsv`) and keep them committed.
- It aborts if an id occurs in two out files.
- Procedure: copy the two Extra files to a temporary folder →
  `python3 tools/merge-translation.py --torr` (compare the counts) → real run →
  diff old vs new Extra files (**no old id may be lost**; list the changed
  ids in the DECISIONS file) → `luac5.1 -p` on both files → test suite → in-game
  `/reload` check.
- Results of the 2026-11-18 run: `QuestExtra.lua` 133 → 359 rows,
  `NpcExtra.lua` 1,139 → 3,891 rows, 0 lost, 24 changed (21 former fragments
  and 3 quests with new wording).

## Quick reference (the whole loop for one round)

```
python3 -m unittest discover -s tests                # once per round
wc -l translation/questcache-en.tsv translation/creaturecache-en.tsv
python3 tools/select-untranslated.py translation/questcache-en.tsv \
        translation/creaturecache-en.tsv
# Include these optional inputs to create game-object and page-text batches:
python3 tools/select-untranslated.py translation/questcache-en.tsv \
  translation/creaturecache-en.tsv translation/gameobjectcache-en.tsv \
  translation/pagetextcache-en.tsv
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
# Optional gameobjects-batch / pagetext-batch use matching -sv.tsv files and
# validate with `gameobjects` / `pagetext`; these are not merged into Data/ yet.
# Game-object batches cannot pass validation (repeated ids by design).
# STOP -> hand translation/out/ + review DECISIONS to the merge step, which is
# a separate task: archive first, then
#   cp Data/QuestExtra.lua Data/NpcExtra.lua /tmp/   # for the before/after diff
#   python3 tools/merge-translation.py --torr
#   python3 tools/merge-translation.py
#   luac5.1 -p Data/QuestExtra.lua && luac5.1 -p Data/NpcExtra.lua
#   python3 -m unittest discover -s tests
# UI text: parse-uidump.py -> translate -> Data/UiExtra.lua ->
#   lua5.1 tools/check-ui-translation.lua <en.tsv> <sv.tsv>
```