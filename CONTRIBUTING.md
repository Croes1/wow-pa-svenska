# Contributing

Thanks for your interest in improving WoW på Svenska!

Contributions of all kinds are welcome, whether you want to correct a translation, collect missing game text, improve the addon or help with development.

## Reporting translation errors

The easiest way to report an incorrect translation is in-game:

1. Hover over the text or open the dialogue containing the error.
2. Type `/wps fel <comment>` in chat.
3. Reload the interface with `/reload` or log out to save the report.
4. Find `WTF/Account/<account>/SavedVariables/wow_pa_svenska.lua`.
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

The relevant files are `questcache.wdb` and `creaturecache.wdb` (the client also writes `gameobjectcache.wdb` and `pagetextcache.wdb`). These files help identify missing translations.

## Where translations live

The files in `Data/` are what the addon loads, and they are edited directly. Nothing is generated from another database.

| File | Table | Entry |
|---|---|---|
| `Data/Quest.lua` | `quest` | `[id]={t,d,o,p,c,l}` title, description, objectives, progress, completion, tracker lines |
| `Data/Npc.lua` | `npc` | `[id]="Name"` |
| `Data/Item.lua` | `item` | `[id]={h,n,d}` |
| `Data/Spell.lua` | `spell` | `[id]={e,ea,n,d,a,c}` |
| `Data/Gossip.lua` | `gossip` | `["<length>_<djb2 hex>"]="Text"` |
| `Data/Zone.lua` | `zone` | `["English"]="Svenska"` |
| `Data/Ui.lua` | `ui` | `["English"]="Svenska"` (strings with `%s`/`%d` are format strings) |
| `Data/Glossary.lua` | `names_*`, `qtext` | `["English"]="Svenska"`, plus the terminology decisions at the top |

Each file starts with a comment that explains its table. Keep one entry per line, in the style already used. `python3 tools/datalua.py Data/*.lua` verifies that a file is in the format the tools understand.

To look something up (English or Swedish text, keys, comments):

```bash
python3 tools/check-data.py search "Stormwind"                  # anywhere
python3 tools/check-data.py search oger --lang comment          # terminology notes only
python3 tools/check-data.py search "Defias" --table names_npc   # one table
python3 tools/check-data.py gossip-key "Greetings, $N."         # the Gossip.lua key of an English text
```

## Contributing translations

For a few corrections, edit the entry in `Data/` and open a pull request. For a larger batch of new text, use the translation round below. In both cases:

1. Look the term up first (`check-data.py search`) and follow the style and terminology below.
2. Never overwrite a reviewed translation without a reason.
3. Run the checks (`check-data.py`, the tests, `luac5.1 -p Data/*.lua`) and read the diff.
4. A maintainer reviews the change before it is released.

### A translation round

All intermediate files stay in a work directory **outside** the repository. The examples use `~/wow-pa-svenska-work` (call it `$WORK`); any path will do. The tools that write intermediate files require `--work-dir` or explicit paths, print what they read and wrote, and refuse to overwrite earlier worklists or batches without `--force`. Keep the work directory until the translations are merged and committed.

```text
$WORK/
├── cache/         <- combine-wdb.py
├── untranslated/  <- select-untranslated.py
├── batches/       <- make-batches.py  (batches/review/ <- verify-segmentation.py)
├── segmented/     <- quests only, written by the translator
└── out/           <- the finished -sv.tsv files
```

**1. Collect.** Turn the client caches into TSV (files go to `$WORK/cache/`):

```bash
python3 tools/combine-wdb.py -r <folder-with-wdb-files> [<another-folder> ...] --work-dir "$WORK" [--force]
# one file at a time:  python3 tools/parse-wdb.py <file.wdb> tsv <out.tsv>
```

This gives `questcache-en.tsv`, `creaturecache-en.tsv`, `gameobjectcache-en.tsv` and `pagetextcache-en.tsv`.

**2. Select** what is not translated yet. The tool reads the real `Data/Quest.lua` and `Data/Npc.lua`; it writes a new numbered worklist per kind and never changes an earlier one:

```bash
python3 tools/select-untranslated.py "$WORK/cache/questcache-en.tsv" "$WORK/cache/creaturecache-en.tsv" --work-dir "$WORK"
# add "$WORK/cache/gameobjectcache-en.tsv" "$WORK/cache/pagetextcache-en.tsv" for those worklists too
```

**3. Batch** the worklists (10 quests, 150 NPCs per file; `--force` replaces existing batches):

```bash
python3 tools/make-batches.py --work-dir "$WORK"
```

**4. Segment the quests** (quests only). The cache holds each quest as one string, with title, objectives, description, progress and reward glued together. Split it into the six columns `id title objectives description progress reward` with the segmentation prompt below, write `$WORK/segmented/quests-batch-NN-en-segmented.tsv` and check it:

```bash
python3 tools/verify-segmentation.py "$WORK/batches/quests-batch-NN.tsv" "$WORK/segmented/quests-batch-NN-en-segmented.tsv"
```

It proves that the five fields put back together are exactly the source text. It cannot prove that the text is in the right column. Rows that are probably incomplete (empty title, text that starts mid-sentence) are routed to `$WORK/batches/review/` (a third argument chooses another path). A person places those by hand and writes the decision down in the work directory.

**5. Translate** with the translation prompt below, from the segmented file (quests) or the batch (NPCs), and write `$WORK/out/quests-batch-NN-sv.tsv` or `npcs-batch-NN-sv.tsv`. Then validate:

```bash
python3 tools/validate-batch.py "$WORK/batches/quests-batch-NN.tsv" "$WORK/out/quests-batch-NN-sv.tsv" quests    # or npcs
python3 tools/fix-empty-columns.py "$WORK/segmented/quests-batch-NN-en-segmented.tsv" "$WORK/out/quests-batch-NN-sv.tsv"
```

`validate-batch.py` checks the ids and their order, the column count and that every placeholder occurs as many times as in the source (exit 1 on errors; warnings need a look). `fix-empty-columns.py` restores trailing empty columns that were dropped, only where the English reference is empty too, and rewrites only the file it is given; run the validator again afterwards. Neither tool can tell whether the Swedish is good.

**6. Merge** into `Data/`. Always run `--dry-run` first and read the additions, skips (keys already in `Data/`) and rejections:

```bash
python3 tools/merge-translation.py quests --input "$WORK/out" --dry-run
python3 tools/merge-translation.py quests --input "$WORK/out"
python3 tools/merge-translation.py npcs   --input "$WORK/out" --dry-run
python3 tools/merge-translation.py npcs   --input "$WORK/out"
```

`--input` is a file or a directory (every `quests-batch-NN-sv.tsv` or `npcs-batch-NN-sv.tsv` in it). `--data-dir DIR` points at another set of Data files. An existing key is never overwritten; `--overwrite` replaces it and lists every old and new value, for a deliberate correction only. A structural error (wrong column count, duplicate or non-numeric id) stops the run before anything is written. New entries go in deterministically (by id, in place), and the file is replaced atomically after the result has been re-parsed and syntax checked. Game objects and page text have no table in the addon, so the tool refuses them; keep that work in the work directory.

In a TSV a line break is written as `\n` or `\r\n` (and a tab as `\t`), because a row is one line; the merge stores each as a real line break. `$B` stays `$B`. Quotes and lone backslashes are taken literally. Do not write `\\r\\n` into a `Data` file by hand: `check-data.py` reports a literal backslash-r or backslash-n as an error.

**UI strings** follow the same pattern. `/wps dump` in game collects the strings that are not translated yet into `WPSDB.uiDump`:

```bash
python3 tools/parse-uidump.py "<WTF>/Account/<account>/SavedVariables/wow_pa_svenska.lua" -o "$WORK/ui/dump-YYYY-MM-DD-en.tsv" [--force]
# translate: a second file "$WORK/ui/dump-YYYY-MM-DD-sv.tsv" with  id<TAB>swedish
lua5.1 tools/check-ui-translation.lua "$WORK/ui/dump-YYYY-MM-DD-en.tsv" "$WORK/ui/dump-YYYY-MM-DD-sv.tsv"
python3 tools/merge-translation.py ui --input "$WORK/ui/dump-YYYY-MM-DD-en.tsv" --sv "$WORK/ui/dump-YYYY-MM-DD-sv.tsv" --dry-run
python3 tools/merge-translation.py ui --input "$WORK/ui/dump-YYYY-MM-DD-en.tsv" --sv "$WORK/ui/dump-YYYY-MM-DD-sv.tsv"
```

A UI key must match the game text character for character, including double and leading spaces; otherwise it never matches.

**7. Check, test, commit.** The loop for every change to `Data/` is **dry-run → merge → check-data → tests → commit**:

```bash
python3 tools/check-data.py              # errors block a merge (exit 1); warnings are hints
python3 -m unittest discover -s tests
luac5.1 -p Data/*.lua
git diff                                 # only the intended additions
git add Data && git commit -m "Add quests from batch NN"   # record the batch and source in the message
```

`check-data.py` reports duplicate keys, empty or malformed entries, missing quest and item fields, lost placeholders, literal `\r\n`, non-canonical entry lines and the same English term translated differently. Its options: `--data-dir DIR`; `check --examples N | --all-warnings`; `search TEXT [--exact] [--case-sensitive] [--lang en|sv|comment|key|any] [--table NAME] [--max N]`; `gossip-key TEXT [--player NAME]`. Run `python3 tools/check-data.py --help` or read the docstring at the top of the file for the full list of checks.

To prove that a change to tools, data structure or comments changes no behaviour, compare what the addon loads, before and after, with the dump written outside the repository:

```bash
lua5.1 tools/dump-runtime.lua > "$WORK/before.tsv"     # before the change
lua5.1 tools/dump-runtime.lua > "$WORK/after.tsv"      # after it
cmp "$WORK/before.tsv" "$WORK/after.tsv"               # a pure refactoring must give no difference;
                                                       # a merge must only add rows
```

Remove completed work from `$WORK` only after the merged translations are committed and verified.

### Intentional differences between translations

`check-data.py` warns (`inconsistent`) when the same English term is translated differently in different entries or tables. Many of these are real mistakes. Some are on purpose, for example a creature name that stays English in a quest but is also the name of a spell. Do not change a translation just to silence the warning. If the difference is deliberate, say so on one of the entries with a trailing comment:

```lua
["Carnage"]="Carnage", -- wps:skillnad creature name, kept English; the spell is "Blodbad"
```

The marker is `wps:skillnad` followed by a reason. The reason is required: a marker without one is itself a warning and silences nothing. It silences the warning for that English term, whatever the case, wherever its entries are, so one marker is enough. The marker only has effect on entries with an English text as key (the `names_*` tables, `zone`, `ui` and `qtext`), not on the id-keyed tables or `gossip`. List all markers with `python3 tools/check-data.py search skillnad --lang comment`.

### Translation guidelines

**Terminology.** The decisions already taken are comments in `Data/Glossary.lua` (the `TERMINOLOGIBESLUT` section at the top and notes on single entries) and in `Data/Ui.lua`. The entries themselves are the glossary: places, factions, creatures and items are in `Data/Glossary.lua`, and the same word should have the same Swedish translation everywhere. Look a term up before you invent a translation, and write a durable decision down as a comment next to the entry. Uncertain translations go to review; never guess.

**Swedish style.**

- Natural, clear Swedish before literal translation, but keep the vocabulary of the Warcraft fantasy (*häxdoktor*, *myrmidon*, *vederstygglighet*).
- Address the player as *du*, never *ni*. A classic quest-giver voice, slightly archaic but natural; do not stack archaisms (*eder*, *sannerligen*) unless the English is formal-epic. Light spoken style for dialect, no phonetic spelling.
- Ellipsis is ` ...` with a space before it. Straight quotation marks (`"`), no typographic quotes and no em-dashes in game text. Decimal comma (`1,5`), localized units (`30 sekunder`, `9 meter`), and a space before percent (`$s1 %`).
- Idioms are translated by meaning, not word for word (*Other Fish to Fry* = *Annat att ta itu med*).
- Do not invent names that are missing from the source: *Lord Admiral* without a name is *Herr Amiral*.
- Fixed vocabulary:
  - classes: Warrior = Krigare, Mage = Magiker, Priest = Präst, Rogue = Skurk, Warlock = Häxmästare, Hunter = Jägare, Paladin, Shaman = Schaman, Druid;
  - races: Human = Människa, Dwarf = Dvärg, Night Elf = Nattalv, Gnome = Gnom, Orc = Orch, Undead = Odöd, Tauren, Troll;
  - reputation: Hated = Hatad, Hostile = Fientlig, Unfriendly = Ovänlig, Neutral, Friendly = Vänlig, Honored = Ärad, Revered = Vördad, Exalted = Upphöjd;
  - gold / silver / copper = guld / silver / koppar.
  - *Rogue* is always *Skurk* (class, villain, the Undercity district, mob names). The shipped exceptions are *scalawag* = *skälm* and the harpy *Roguefeather*, which follows the shipped data. If unsure, keep the English word and let a reviewer decide.
- Place names are translated as in the glossary (Stormvind, Järnsmedjan, Mörkby, Skymningsskogen, Våtmarkerna, Understaden, Kargmarkerna). Find them with `check-data.py search`.
- System messages follow the templates in `Chat.lua` (*Ditt anseende hos %s har ökat.*), not free wording.
- dungeon/instance → *instans*; raid → *raid*, plural *raids* (*Instanser & Raids*). Group size is written *N-manna*: *10-manna raids*, *5-manna instanser* (not *N-mans*).

**What stays untranslated.**

- **Personal names** stay in English (*Doctor Marsh*, *Karu*, *Demnul Farmountain*, *Ana'thek*). A rank or title in front of the name is translated: *Guard Thomas* → *vakt Thomas*, *Deputy Feldon* → *Konstapel Feldon*.
- A creature with a name of its own is a personal name: *Carnage* stays *Carnage* in the quest, while the spell *Carnage* is *Blodbad*.
- **Descriptive names** (a creature type, a group, an item) are translated into natural Swedish compounds following the glossary: *Forest Spider* → *Skogsspindel*, *Forlorn Spirit* → *Övergiven ande*, *Defias Pillager* → *Defiasplundrare*.
- A tribe or clan name keeps its name and joins its title with a hyphen: *Vissenbark-yxkastare*, *Boulderfist-oger*, *Slitherblade-myrmidon*.
- Two tribes are decided exceptions and are translated: *Skullsplitter* = *Skallkrossarna* (*Skallkrossar-krigare*, *Skallkrossarbete*) and *Timbermaw* = *Skogsbjörnarna* (*Skogsbjörnarnas Näste*, and *skogsbjörns-* in compounds such as *Skogsbjörnstunika*). Do not rename any other tribe without a decision.

**Tokens and markup.** The addon and the game client interpret these. They are never translated, never added and never dropped; copy them byte for byte. The validators count them per row.

- Player, class and race: `$N $n $C $c $R $r`; line breaks `$B $b`.
- Gender switches such as `$Gman:kvinna;` and `$g...;`, and plural words `$l...;`.
- Spell variables: `$s1 $d $t1 $w1`, formulas `${$m2$*$<frostdamage>}`, `$?a14748[...][...]`, `$<frostdamage>`.
- Objective counters `#/#` (*#/# Murlocfena* becomes *3/10 Murlocfena* in game), format specifiers `%s %d` (same count and meaning), colour and link codes `|cffrrggbb...|r`, `|Hplayer:%s|h[%s]|h`.
- Unknown tokens such as `$2oa` (the Craftsman's Writ quests) belong to the game client. Copy them as they are; how the client interprets `$2oa` is not confirmed.
- Reordering is allowed only where Swedish grammar requires it. The text around a token may differ, the token itself may not.
- Never write a gossip key by hand; compute it with `check-data.py gossip-key`.

**Word choices that have been decided** (the rest are in the comments in `Data/`): *oger* (en oger, ogern, oger, ogerna; never *ogre*, *ogrer*, *ograr*); *supplies* = *förnödenheter*; *bra* / *god* (*God träskmat*); *tam* rather than *foglig* for wild animals; *skeppsvrak* only for a destroyed ship; *från X* (origin) and *till X* (destination) are different directions, so check the source.

### The translation prompt

Translations are written by a person or by an AI agent working in the editor, **never through a translation API** (see Development). Paste this with the TSV rows. Terms and decisions come from `Data/` (`check-data.py search`); attach the relevant entries, not the whole glossary.

```text
You translate World of Warcraft (classic era) game text from English to Swedish
for the translation addon "WoW på Svenska".

TERMS
- Follow the existing translations in Data/ (names, places, factions, items)
  exactly; prefer an existing entry over your own wording. If an entry disagrees
  with shipped data for the same proper noun, keep the shipped form and say so.
- Fixed vocabulary: Warrior=Krigare, Mage=Magiker, Priest=Präst, Rogue=Skurk,
  Warlock=Häxmästare, Hunter=Jägare, Paladin, Shaman=Schaman, Druid,
  Human=Människa, Dwarf=Dvärg, Night Elf=Nattalv, Gnome=Gnom, Orc=Orch,
  Undead=Odöd, Tauren, Troll; Hated=Hatad, Hostile=Fientlig, Unfriendly=Ovänlig,
  Neutral, Friendly=Vänlig, Honored=Ärad, Revered=Vördad, Exalted=Upphöjd;
  gold/silver/copper = guld/silver/koppar.
- Personal names stay in English; a rank in front of the name is translated
  ("Guard Thomas" -> "vakt Thomas"). A creature with its own name stays English.
  Descriptive names (types, groups) become natural Swedish compounds:
  "Forest Spider" -> "Skogsspindel". Tribe name + title takes a hyphen:
  "Boulderfist-oger". Exceptions: Skullsplitter = Skallkrossarna,
  Timbermaw = Skogsbjörnarna (Skogsbjörnarnas Näste, skogsbjörns- in compounds).

TOKENS - copy byte for byte, never translate, add or drop (reordering only if
Swedish grammar requires it):
- $N $n $C $c $R $r, line breaks $B $b, gender switches $Gman:kvinna; and $g...;
- spell variables $s1 $d $t1 $w1, ${$m2$*$<frostdamage>}, $?a14748[...][...]
- the counter #/#, format specifiers %s %d, colour/link codes |cffrrggbb...|r
  and |H...|h[...]|h
- unknown tokens such as $2oa belong to the game client: copy them as they are.

STYLE
- Address the player as "du" (never "ni"). Classic quest-giver voice, natural
  Swedish first; do not stack archaisms.
- Ellipsis " ..." with a space before it, straight quotation marks ("), no em-dashes,
  decimal comma ("1,5"), "30 sekunder", and a space before percent ("$s1 %").
- Idioms are translated by meaning, not word for word.
- Never invent names or text that is not in the source.

OUTPUT
- Output only the TSV rows: the same ids in the same order, the same columns
  as the input, no code fences, no headings, no commentary, no blank lines.
- Quest rows: id, title, objectives, description, progress, reward (six
  columns). A field that is empty in English stays empty.
- NPC rows: input id, name, title; output only id, Swedish name. The title is
  reference only.
- A line break inside a cell is written as \n; keep it as \n.
- If you cannot translate a field with confidence, keep the English text in
  that field. Never leave a whole row empty.
```

The segmentation prompt for step 4 (quests only):

```text
You split World of Warcraft (classic era) quest text that is stored as ONE
string: title, objectives, description, progress text and reward dialogue glued
together with no delimiter. You do NOT translate - you only split.

INPUT: TSV rows id<TAB>body. A single space often precedes the title. Some rows
are fragments: they start mid-sentence, with '<' or with a $-token, and have no
title.

OUTPUT: exactly one row per input row:
id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward

- title = the quest name; objectives = the "X wants you to ..." / "Bring N ... to Y"
  summary; description = the longer story text; progress = the mid-quest
  hand-in line if present; reward = the turn-in dialogue, else empty.

RULES
1. The five fields, concatenated in order, must reproduce the body exactly
   (whitespace at the very start or end may be dropped). Add, drop and reorder
   nothing; do not touch spaces inside the text or split words.
2. A field that does not exist stays EMPTY. Never invent a title, objectives,
   progress or reward. A fragment has an empty title.
3. If you cannot find a boundary, keep the text in the earlier field.
4. Game tokens ($B, $b, $c, $n, $N, $2oa, ...) stay attached to their text.
5. Output only the TSV rows, in the same order, with no commentary.
```

## Development

For addon code and tooling changes:

- Follow the existing Lua and Python conventions.
- Keep changes focused and avoid unnecessary dependencies. The tools use only the Python standard library.
- **Do not introduce external translation APIs or network-dependent translation tools.** The translator is a person or an agent in the editor; the tools stay offline.
- Preserve compatibility with the WoW Forever client.
- Avoid modifying existing translations when working on unrelated functionality.
- Tests must not depend on files outside the repository; put small test data in `tests/fixtures/`.

Before submitting changes, run the test suite, the data check and the Lua syntax check:

```bash
python3 -m unittest discover -s tests
python3 tools/check-data.py
luac5.1 -p Data/*.lua
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
