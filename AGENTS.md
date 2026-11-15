# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project

Wow på Svenska is a World of Warcraft Classic Era addon for WoW Forever. It replaces English game text with Swedish on an enUS client.

- `*.lua` — addon code and translation data.
- `Data/` — game text databases.
- `translation/` — translation sources, glossary, prompts and batches.
- `tools/` — offline parsing, translation and validation tools.
- `tests/` — automated tests.

## Rules

1. **No external APIs or network calls.** Translation work must use the repository's offline tools. Do not introduce translation APIs, external AI services, HTTP requests or API credentials.
2. **Preserve existing translations.** Never overwrite reviewed translations. Generated data files must not be edited manually during translation rounds. Merging translations into game data is a separate, explicitly reviewed step.
3. **Preserve game formatting.** Keep all placeholders, color codes, links, escape sequences and game-specific tokens exactly as they appear in the source.
4. **Do not guess.** If a translation or field placement is uncertain, leave it for review rather than inventing text.
5. **Follow the existing project conventions.** Avoid unnecessary dependencies, generated files, unrelated refactoring and duplicated documentation.

## Before making changes

1. Check the current Git status and inspect existing changes.
2. Read `translation/PIPELINE.md` before working on translations.
3. Read `translation/PROMPT-GEMMA.md` for segmentation and translation instructions.
4. Read `translation/PROMPT-translation.md` for Swedish writing conventions.
5. Check `translation/glossary-core.tsv` and relevant review decisions for established terminology.
6. Run the existing tests before making substantial changes:

   ```bash
   python3 -m unittest discover -s tests
   ```

## Translation workflow

Follow `translation/PIPELINE.md` for the complete workflow, including:

- Importing new English game text.
- Selecting untranslated entries and creating batches.
- Segmenting and validating source text.
- Translating and reviewing entries.
- Running validation before merging.

Do not skip validation or start a new translation round while an earlier round is unfinished.

## After changes

- Run relevant tests and validation tools.
- Check that existing translations and game formatting are preserved.
- Review the Git diff for unintended changes.
- Do not merge generated translations into `Data/` unless explicitly requested.

Keep changes focused and documentation concise. When in doubt, follow the existing implementation rather than introducing a new approach# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project

Wow på Svenska is a World of Warcraft Classic Era addon for WoW Forever. It replaces English game text with Swedish on an enUS client.

- `*.lua` — addon code and translation data.
- `Data/` — game text databases.
- `translation/` — translation sources, glossary, prompts and batches.
- `tools/` — offline parsing, translation and validation tools.
- `tests/` — automated tests.

## Rules

1. **No external APIs or network calls.** Translation work must use the repository's offline tools. Do not introduce translation APIs, external AI services, HTTP requests or API credentials.
2. **Preserve existing translations.** Never overwrite reviewed translations. Generated data files must not be edited manually during translation rounds. Merging translations into game data is a separate, explicitly reviewed step.
3. **Preserve game formatting.** Keep all placeholders, color codes, links, escape sequences and game-specific tokens exactly as they appear in the source.
4. **Do not guess.** If a translation or field placement is uncertain, leave it for review rather than inventing text.
5. **Follow the existing project conventions.** Avoid unnecessary dependencies, generated files, unrelated refactoring and duplicated documentation.

## Before making changes

1. Check the current Git status and inspect existing changes.
2. Read `translation/PIPELINE.md` before working on translations.
3. Read `translation/PROMPT-GEMMA.md` for segmentation and translation instructions.
4. Read `translation/PROMPT-translation.md` for Swedish writing conventions.
5. Check `translation/glossary-core.tsv` and relevant review decisions for established terminology.
6. Run the existing tests before making substantial changes:

   ```bash
   python3 -m unittest discover -s tests
   ```

## Translation workflow

Follow `translation/PIPELINE.md` for the complete workflow, including:

- Importing new English game text.
- Selecting untranslated entries and creating batches.
- Segmenting and validating source text.
- Translating and reviewing entries.
- Running validation before merging.

Do not skip validation or start a new translation round while an earlier round is unfinished.

## After changes

- Run relevant tests and validation tools.
- Check that existing translations and game formatting are preserved.
- Review the Git diff for unintended changes.
- Do not merge generated translations into `Data/` unless explicitly requested.

Keep changes focused and documentation concise. When in doubt, follow the existing implementation rather than introducing a new approach..
