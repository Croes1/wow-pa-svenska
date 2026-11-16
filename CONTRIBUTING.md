# Contributing

Thanks for your interest in improving WoW på Svenska!

Contributions of all kinds are welcome, whether you want to correct a translation, collect missing game text, improve the addon or help with development.

## Reporting translation errors

The easiest way to report an incorrect translation is in-game:

1. Hover over the text or open the dialogue containing the error.
2. Type `/wps fel <comment>` in chat.
3. Reload the interface with `/reload` or log out to save the report.
4. Find `WTF/Account/<account>/SavedVariables/WPSDB.lua`.
5. Attach the file to a [GitHub Issue](https://github.com/Croes1/wow-pa-svenska/issues).

Include a short explanation of what you think the correct translation should be.

You can also open an issue directly on GitHub.

## Collecting missing game text

Quest and NPC data is collected through the English game client.

You can help by:

1. Playing with the client language set to **English (enUS)**.
2. Opening quests and talking to NPCs as you play.
3. Allowing the game to populate its cache files under `Cache/WDB`.
4. Closing the game and sharing the collected cache files with the maintainer.

The relevant files are:

- `questcache.wdb`
- `creaturecache.wdb`

These files help identify missing translations.

## Contributing translations

If you want to work directly with translations:

1. Check `translation/glossary-core.tsv` for established terminology.
2. Follow the Swedish writing conventions in `translation/PROMPT-translation.md`.
3. Follow the workflow in `translation/PIPELINE.md`.
4. Validate your changes using the provided tools.
5. Have translations reviewed before they are merged into the addon.

### Translation guidelines

- Prefer natural, clear Swedish over literal translations.
- Keep terminology consistent with the existing glossary.
- Preserve character names and established Warcraft terminology where appropriate.
- Keep placeholders, color codes, links and game-specific formatting intact.
- Never invent missing source text or guess the meaning of incomplete records.
- Leave uncertain translations for review.

## Development

For addon code and tooling changes:

- Follow the existing Lua and Python conventions.
- Keep changes focused and avoid unnecessary dependencies.
- Do not introduce external translation APIs or network-dependent translation tools.
- Preserve compatibility with the WoW Forever client.
- Avoid modifying existing translations when working on unrelated functionality.

Before submitting changes, run the test suite:

```bash
python3 -m unittest discover -s tests
```

Review your changes with:

```bash
git diff
git status
```

## Pull requests

For code, documentation and translation improvements, pull requests are welcome.

1. Fork the repository.
2. Create a branch for your changes.
3. Make and test your changes.
4. Commit and push your branch.
5. Open a pull request against this repository.

Use a clear title describing what you changed.

Include the following in your pull request:

- **What:** A short description of the changes.
- **Why:** What problem does it solve?
- **Testing:** What did you test?
- **Notes:** Anything that needs additional review.

Keep pull requests focused. Smaller changes are easier to review and merge.

## Questions and feedback

- [Report a bug or suggest an improvement](https://github.com/Croes1/wow-pa-svenska/issues).
- [Browse existing issues](https://github.com/Croes1/wow-pa-svenska/issues).

Thanks for helping make Azeroth a little more Swedish!


