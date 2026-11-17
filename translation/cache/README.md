# translation/cache — translate quest and NPC text from client caches

Plain-English guide to collecting quest and creature names from the WoW
Forever client, preparing translation batches, and translating them offline.
The scripts extract and check data; Swedish translations are written by a
human or the VS Code chat agent following the project rules. No translation
API or external service is used.

## How it works

The enUS client saves quest and creature data to WDB cache files while you
play. The tools turn those files into TSVs, select IDs that are not already
in the addon data, and split the missing rows into batches:

```text
client WDB files → cache TSVs → untranslated TSVs → batches
    → segment quests → translate → validate and review → ready for merge
```

## The workflow

### 1. Collect — in the game

Play on the enUS client. It writes cache files without an addon. When you are
finished, quit the game before copying the files so the caches are up to date.
The usual location is under:

```text
World of Warcraft/_forever_/Cache/WDB/
```

Collect `questcache.wdb` and `creaturecache.wdb`.

### 2. Extract — make the English cache TSVs

From the repository root, run the parser with its `tsv` mode:

```bash
python3 tools/parse-wdb.py \
  ".../Cache/WDB/questcache.wdb" tsv translation/questcache-en.tsv
python3 tools/parse-wdb.py \
  ".../Cache/WDB/creaturecache.wdb" tsv translation/creaturecache-en.tsv
```

The quest TSV has `id<TAB>text`; each quest is one long string with its title,
objectives, description, progress text, and reward dialogue joined together.
The creature TSV has `id<TAB>name<TAB>title`. Keep the English text and IDs
unchanged. These are source caches, not translation output.

### 3. Select missing entries and make batches

Compare the cache IDs against the translations already shipped in
`Data/Quest.lua` and `Data/Npc.lua`:

```bash
python3 tools/select-untranslated.py \
  translation/questcache-en.tsv translation/creaturecache-en.tsv
python3 tools/make-batches.py
```

This writes `translation/quest-not-translated.tsv` and
`translation/npcs-not-translated.tsv`, then batches them under
`translation/batches/` (10 quests or 150 NPCs per batch). Check that the
`overlapp` counts printed by the selector are greater than zero; this helps
confirm the cache IDs match the IDs in the addon data.

These commands rewrite the work lists and batch files. Finish the current
round before generating batches from changed caches. If a round must be
restarted, archive its segmented/output/review files first and keep the
`DECISIONS-*.md` review notes; batch numbers can change when the input set
changes.

### 4. Translate one batch at a time

Read `translation/PROMPT-GEMMA.md`,
`translation/PROMPT-translation.md`, and `translation/glossary-core.tsv`
before translating. Search `translation/glossary-all.tsv` for additional
terms when needed. Preserve IDs, row order, empty fields, and all game tokens.
Do not invent missing source text; leave uncertain cases for review.

**Quests:** split each `id<TAB>text` row into six fields in this order:
`id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward`.
Save the English split as
`translation/segmented/quests-batch-XX-en-segmented.tsv`, then verify it:

```bash
python3 tools/verify-segmentation.py \
  translation/batches/quests-batch-XX.tsv \
  translation/segmented/quests-batch-XX-en-segmented.tsv
```

Continue only when it reports `RESULTAT: OK`. Review any rows routed to
`translation/batches/review/quests-batch-XX-en-review.tsv`; record placement
decisions in a dated `DECISIONS-YYYY-MM-DD.md` file. Then translate the
segmented fields to Swedish and save them, with the same six columns, as
`translation/out/quests-batch-XX-sv.tsv`.

**NPCs:** translate the name in each `npcs-batch-XX.tsv` row and save
`id<TAB>swedish-name` to `translation/out/npcs-batch-XX-sv.tsv`. The English
title is reference only and must not be included in the output. Personal names
usually stay unchanged; translate descriptive creature names according to
the glossary and shipped terminology.

### 5. Validate and review

Validate each translated batch:

```bash
python3 tools/validate-batch.py \
  translation/batches/quests-batch-XX.tsv \
  translation/out/quests-batch-XX-sv.tsv quests
python3 tools/validate-batch.py \
  translation/batches/npcs-batch-XX.tsv \
  translation/out/npcs-batch-XX-sv.tsv npcs
```

`RESULTAT: OK` means the IDs, columns, order, and game-token counts passed
the automated checks. It does not judge Swedish quality. Review warnings,
check names against the glossary, and have a human quality-check the Swedish.
Do not merge unreviewed output into `Data/`.

Run the test suite when tools have changed or when in doubt:

```bash
python3 -m unittest discover -s tests
```

### 6. Stop before merge

When every batch has passed validation and human review, the TSV output and
review decisions are ready for a separate merge task. This workflow does not
edit `Data/Quest.lua` or `Data/Npc.lua`; follow the merge instructions in
`translation/PIPELINE.md` separately.

## Tools

| Tool | Purpose |
|---|---|
| `tools/parse-wdb.py` | Client WDB cache to English TSV |
| `tools/select-untranslated.py` | Compare cache IDs with shipped translations |
| `tools/make-batches.py` | Split untranslated work lists into batches |
| `tools/verify-segmentation.py` | Check quest text is partitioned without loss |
| `tools/validate-batch.py` | Check translated batch IDs, columns, and tokens |

For detailed edge cases and acceptance rules, see
`translation/PIPELINE.md` and `AGENTS.md`.