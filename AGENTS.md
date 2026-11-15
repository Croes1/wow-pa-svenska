# AGENTS.md — read me first (AI agents working in this repo)

Wow på Svenska: a WoW (classic era) addon that swaps English game text for
Swedish while playing (enUS client). This folder holds the shipped
`Data/*.lua` databases (generated — never edit them by hand), the in-game Lua
code, and the translation-round machinery under `translation/`.

## The three hard rules

1. **NO translation APIs. Ever.** Do not call any external AI service, model
   or translation API — no LLM endpoints, no HTTP calls of any kind. **You —
   the agent in the VS Code chat — are the translator**: you read the TASK
   blocks, segment the English
   yourself, write the Swedish yourself, and save it straight to the TSV
   files. The only programs you may run are the offline, network-free tools
   in `tools/` (checkers, batchers, parsers). The old API runner
   (`tools/run-gemma.py`) and the API key (`.env`) were removed on
   2026-11-15 on purpose — do not re-add them or any substitute.
2. **Never touch `Data/*.lua` during a translation round.** They are
   generated files containing years of reviewed Swedish; every existing
   translation must be preserved. The merge of finished TSVs into them is a
   separate, separately reviewed task — and the translation loop **stops
   before it**.
3. **Never invent text.** Segmentation (TASK A) is an exact partition of the
   source row; translation (TASK B) keeps every game token (`$B`, `$b`, `#/#`,
   `%s`, `$2oa`, color/link markup) byte for byte. If you are unsure about a
   field: leave it empty/English and route the row to review.

## Read next, in this order

1. `translation/PIPELINE.md` — the full loop: how new data arrives, the
   offline tools, the per-batch steps (segment → verify → review → translate
   → validate), the acceptance gate, and the STOP boundary.
2. `translation/PROMPT-GEMMA.md` — the TASK A (segment), TASK B (translate)
   and NPC-variant blocks you must follow verbatim (the file name is
   historical; no "Gemma chat" is involved anymore).
3. `translation/PROMPT-translation.md` — style rules for the Swedish prose
   (address the player as "du", ellipsis as " ...", straight quotes,
   glossary-first naming, …).
4. `translation/batches/review/DECISIONS-2026-11-15.md` — the recorded
   field-placement and terminology decisions (fragment rows, writs,
   Skullsplitter etc.) — follow them for consistency.

## How new data arrives in this repo

New English data comes from the enUS client's own WDB caches
(`Cache/WDB/questcache.wdb`, `Cache/WDB/creaturecache.wdb`) — written
automatically while playing, no addon involved. The maintainer converts them
with `tools/parse-wdb.py` into two TAB-separated caches in `translation/`:

- `translation/questcache-en.tsv` — `id<TAB>text` (one glued line per quest:
  title+objectives+description+progress+reward)
- `translation/creaturecache-en.tsv` — `id<TAB>name<TAB>title`

(A voluntary in-game **Collector** addon is planned but does not exist yet;
if it one day appears, treat its SavedVariables dump as raw input only —
the WDB route above is what works today.)

- `translation/questcache-en.tsv` — `id<TAB>text` (one glued line per quest:
  title+objectives+description+progress+reward)
- `translation/creaturecache-en.tsv` — `id<TAB>name<TAB>title`

Plus, from time to time: `/wps fel` reports — players are told to `/reload` (or
log out) and then send the file
`WTF/Account/<account>/SavedVariables/WPSDB.lua`; the maintainer copies the
`WPSDB.reports` table out of it. Game-data exports (items/spells/zones from
wago.tools or cmangos) — the latter arrive as *maintainer* edits to `Data/`,
never as part of your round.

## What to say to the agent (one-liner, next data round)

> "Ny data är sparad i translation/questcache-en.tsv (+ creaturecache-en.tsv).
> Läs AGENTS.md och translation/PIPELINE.md och kör nästa översättningsrunda."

## What the agent does BEFORE translating anything

1. Read `AGENTS.md` → `translation/PIPELINE.md` → the TASK/style files above.
2. Sanity-check the new caches (UTF-8, TAB-separated, column counts, a few
   eyeballed rows).
3. Run `python3 -m unittest discover -s tests` once (must end `OK`).
4. Run `python3 tools/select-untranslated.py <questcache-en.tsv>
   <creaturecache-en.tsv>` — regenerates
   `translation/quest-not-translated.tsv` / `npcs-not-translated.tsv`
   (watch the `overlapp > 0` confirmation).
5. Run `python3 tools/make-batches.py` — regenerates
   `translation/batches/*.tsv` (10 quests / 150 NPCs per file). This is the
   ground truth for the whole round; check `wc -l translation/batches/*.tsv`.
6. Heed the **stale rule** in PIPELINE.md (finish/archive the old round
   before pulling new data).
7. Only now pick the first unfinished batch and start TASK A.

## Status (2026-11-15)

- The 2026-11-15 round is complete: 1 139 NPC rows and 133 quest rows
  (batches 01–14) translated and verified by the offline checkers; the 5
  stubborn rows (79677, 586, 5763, 94221, 98248) were done by hand — see
  `translation/batches/review/DECISIONS-2026-11-15.md`.
- The old API machinery (runner, tests, key, queue scripts) was removed.
- **MERGED (2026-11-15):** `tools/merge-translation.py` created
  `Data/QuestExtra.lua` (+133 quests) and `Data/NpcExtra.lua` (+1 139 names)
  and `.toc` loads both files after their main Data files. Verified with
  lua5.1 (parse + runtime WPS-stub check, `if LQ[id] == nil` guard so
  reviewed Data/*.lua can never be overwritten). Rollback = remove those two
  files + the two `.toc` lines. Next loop restarts at Loop Point 1 when new
  cache data arrives.