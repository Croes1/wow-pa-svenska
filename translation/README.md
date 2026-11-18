# Translation data

This folder holds the English source data, the Swedish output, and the glossary. This page covers how new game text gets in. The full step-by-step process is in [PIPELINE.md](PIPELINE.md).

## 1. Collect the cache files

Play on the enUS client. It saves text by itself into `Cache/WDB/enUS/` in the WoW folder. You don't need an addon.

The cache exports currently used for translation work are:

- `questcache.wdb`
- `creaturecache.wdb`
- `gameobjectcache.wdb`
- `pagetextcache.wdb`

`npccache.wdb` and `petitioncache.wdb` are recognized by the parser, but the
current client files are empty and produce header-only TSVs.

Quit the game before copying them. The client writes the files when it exits.

Set a variable that points to the folder. Adjust the path to match your install:

```bash
W="../WoW/_forever_/Cache/WDB/enUS"
```

## 2. Convert them to TSV

Run these from the repository root. Each command **overwrites** the matching file in this folder. `git diff` shows what changed.

```bash
python3 tools/parse-wdb.py "$W/questcache.wdb"      tsv translation/questcache-en.tsv
python3 tools/parse-wdb.py "$W/creaturecache.wdb"   tsv translation/creaturecache-en.tsv
python3 tools/parse-wdb.py "$W/gameobjectcache.wdb" tsv translation/gameobjectcache-en.tsv
python3 tools/parse-wdb.py "$W/pagetextcache.wdb"   tsv translation/pagetextcache-en.tsv
```

## 3. Check the result

```bash
wc -l translation/questcache-en.tsv translation/creaturecache-en.tsv \
	translation/gameobjectcache-en.tsv translation/pagetextcache-en.tsv
git diff --stat translation/
```

The files should be UTF-8 and tab-separated. Quests and page text have 2
columns; creatures and game objects have 3.

## 4. Continue with the pipeline

Tell the agent about the new data. It then follows [PIPELINE.md](PIPELINE.md). That covers finding untranslated text, making batches, translating, and checking the results.

Before you start:

- Finish or archive any unfinished round first. Otherwise new batches can end up paired with old output.
- Run `tools/merge-translation.py` only as a separate, reviewed step, and read "Loop Point 4" in [PIPELINE.md](PIPELINE.md) first. It rebuilds `Data/QuestExtra.lua` and `Data/NpcExtra.lua` from `out/`, so any shipped id that is missing from `out/` is dropped. Use `--torr` first and diff the Extra files before and after.
- Archive `out/`, `segmented/` and `batches/` before regenerating batches, and never copy old output back into `out/`.
- To create game-object and page-text worklists as well, pass both additional
	cache TSVs to `tools/select-untranslated.py`, then run `tools/make-batches.py`:
	`python3 tools/select-untranslated.py translation/questcache-en.tsv translation/creaturecache-en.tsv translation/gameobjectcache-en.tsv translation/pagetextcache-en.tsv`.
- Those two categories can be translated and validated, but the addon has no
	runtime data tables or merge path for them yet. Do not treat their `out/`
	files as in-game translations.
- Game-object ids repeat by design in the cache, so game-object batches always fail the id check in `validate-batch.py`. See PIPELINE.md before spending time on them.

## Files in this folder

| File or folder | Contents |
|---|---|
| `questcache-en.tsv`, `creaturecache-en.tsv`, `gameobjectcache-en.tsv`, `pagetextcache-en.tsv` | English source text from the cache |
| `untranslated/` | Numbered worklists made by `select-untranslated.py` (`quests-NNN.tsv`, `npcs-NNN.tsv`, `gameobjects-NNN.tsv`, `pagetext-NNN.tsv`). Never overwritten; `make-batches.py` reads them all. |
| `batches/` | Work batches for the agent |
| `segmented/`, `out/` | Intermediate and Swedish output. `out/` is the only input of `merge-translation.py`; it includes carry-over files (`quests-batch-32-sv.tsv`, `npcs-batch-27-sv.tsv`) that must stay |
| `ui/` | UI text dumps and their Swedish pairs (`dump-*-en.tsv`, `dump-*-sv.tsv`) |
| `batches/review/DECISIONS-*.md` | Placement and terminology decisions per round |
| `glossary-core.tsv`, `glossary-all.tsv` | Approved terms |
| `PROMPT-*.md`, `PIPELINE.md` | Instructions for translation and the process |
