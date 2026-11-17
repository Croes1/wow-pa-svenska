# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project

**WoW på Svenska** is a World of Warcraft Classic Era addon for WoW Forever. It translates English game text into Swedish on an enUS client.

Repository structure:

- `*.lua` — Addon code and translation logic.
- `Data/` — Game text and translation databases.
- `translation/` — Glossary, workflow documentation and test fixtures. Per-round batches and caches are gitignored.
- `tools/` — Scripts for extracting, processing and validating game data.
- `tests/` — Automated tests.

## General rules

1. **Preserve existing translations.** Never overwrite reviewed translations or change established terminology without a reason.
2. **Preserve game formatting.** Keep placeholders, color codes, hyperlinks, escape sequences and game-specific tokens intact.
3. **Do not guess.** Leave uncertain translations or data mappings for review.
4. **Avoid unnecessary changes.** Follow existing conventions and avoid unrelated refactoring, dependencies and generated files.
5. **No external translation services.** Translation and data-processing workflows must use the project's existing tools. Do not introduce external translation APIs or network-dependent services.
6. **Keep documentation focused.** Avoid duplicating information already documented elsewhere.

## Working with translations

Before modifying translation data:

- Check `translation/glossary-core.tsv` for established terminology.
- Follow the Swedish writing conventions in the translation documentation.
- Preserve the original English source text and its formatting.
- Do not overwrite reviewed translations with generated output.
- Keep generated translation batches separate from the addon data until they have been validated and reviewed.

Follow the documented translation workflow in `translation/` when importing, processing, translating or merging game text.

## Development and testing

Before making changes:

1. Check the Git status and inspect existing changes.
2. Understand the existing implementation before modifying it.
3. Run relevant tests before and after substantial changes.

Run the test suite with:

```bash
python3 -m unittest discover -s tests
```

Also run relevant validation tools when modifying translation data or extraction scripts.

## Before finishing

- Review the Git diff for unintended changes.
- Verify that existing translations and game formatting are preserved.
- Run relevant tests and validation tools.
- Do not merge unreviewed generated translations into `Data/`.
- Summarize what changed and mention any tests that could not be run.
