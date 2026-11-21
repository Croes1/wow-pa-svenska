# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project

**WoW på Svenska** is a World of Warcraft Classic Era addon for WoW Forever. It translates English game text into Swedish on an enUS client.

Repository structure:

- `*.lua` — Addon code and translation logic.
- `Data/` — The translations the addon loads. **This is the only permanent source of truth.** Edit these files directly; they are not generated from anything.
- `tools/` — Offline scripts for collecting, selecting, batching, merging, searching and validating translations.
- `tests/` — Automated tests (`tests/fixtures/` holds small test data).

Temporary caches, worklists, batches and review notes live in an external work directory outside the repository (for example `~/wow-pa-svenska-work/`). Never create a work directory inside the repository.

## General rules

1. **Preserve existing translations.** Never overwrite reviewed translations or change established terminology without a reason.
2. **Preserve game formatting.** Keep placeholders (`%s`, `%d`, `$B`, `$N`, `$s1`, `$2oa`, `#/#`), color codes, hyperlinks, escape sequences and game-specific tokens intact. A translation that changes them is wrong.
3. **Do not guess.** Leave uncertain translations or data mappings for review. Never invent source text, IDs or gossip keys.
4. **Avoid unnecessary changes.** Follow existing conventions and avoid unrelated refactoring, dependencies and generated files. The tools use only the Python standard library.
5. **No external translation services.** Do not call any translation API, AI service or network endpoint, and do not add one. The agent or human translator writes the Swedish text; the local tools only collect, validate and merge it.
6. **Keep documentation focused.** Avoid duplicating information already documented elsewhere.

## Working with translations

Before modifying translation data:

- Look up existing terminology with `python3 tools/check-data.py search TERM`. Terminology decisions are comments in `Data/Glossary.lua` (section `TERMINOLOGIBESLUT`) and `Data/Ui.lua`; `--lang comment` searches only those.
- Follow the Swedish style, naming and token rules in [CONTRIBUTING.md](CONTRIBUTING.md).
- Do not overwrite reviewed translations with new output. `merge-translation.py` skips existing keys unless `--overwrite` is given; use that only for a deliberate correction.
- Keep batches and review files in the work directory until they are validated and reviewed.
- Do not merge unreviewed generated translations into `Data/`.

The full round (collect → select → batch → translate → validate → merge) and every tool's options are in [CONTRIBUTING.md](CONTRIBUTING.md). Each tool prints its options with `--help`. In short:

| Tool | Writes |
|---|---|
| `combine-wdb.py`, `parse-wdb.py` | WDB cache → TSV, to the work directory |
| `select-untranslated.py`, `make-batches.py` | worklists and batches, to the work directory |
| `verify-segmentation.py`, `validate-batch.py`, `fix-empty-columns.py` | checks; `verify-segmentation.py` writes a review file only when it routes rows, `fix-empty-columns.py` rewrites the output file it is given |
| `merge-translation.py` | **`Data/*.lua`**; use `--dry-run` first |
| `check-data.py`, `datalua.py`, `dump-runtime.lua`, `check-ui-translation.lua` | read-only |

## Development and testing

Before making changes:

1. Check the Git status and inspect existing changes.
2. Understand the existing implementation before modifying it.
3. Run relevant tests before and after substantial changes.

The loop for any change to `Data/`: `merge-translation.py --dry-run` → merge → `check-data.py` → tests → review the diff → commit.

```bash
python3 tools/check-data.py                  # exit 1 = errors that block a merge
python3 -m unittest discover -s tests
luac5.1 -p Data/*.lua                        # Lua syntax (Lua 5.1)
```

`check-data.py` warns when the same English term has different Swedish translations. If the difference is deliberate, mark one entry with a trailing comment `-- wps:skillnad <reason>`; the reason is required. See [CONTRIBUTING.md](CONTRIBUTING.md). Do not change an existing translation just to silence a warning.

To prove that a change to data structure, tools or comments changed no behaviour, dump what the addon loads before and after and compare: `lua5.1 tools/dump-runtime.lua > before.tsv` (outside the repository), then the same after, and `cmp`. A normal translation merge only adds rows to that dump.

## Before finishing

- Review the Git diff for unintended changes.
- Verify that existing translations and game formatting are preserved.
- Run the tests, `check-data.py` and `luac5.1 -p`.
- Do not merge unreviewed generated translations into `Data/`.
- Summarize what changed and mention any tests that could not be run.
