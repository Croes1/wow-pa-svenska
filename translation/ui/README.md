# translation/ui — how to translate the missing UI texts yourself

Plain-English cheat sheet. No AI services, no internet needed — you type the
Swedish, the tools only check your work.

## How it works (30 seconds)

The addon swaps English for Swedish using one big list: `WPS.L.ui`
(generated `Data/Ui.lua` + the hand-maintained `Data/UiExtra.lua`).
If a text is missing from the list, the game shows English.
So the whole job is: **find the missing texts → add Swedish entries**.

## The 5-step loop

### 1. Collect — in the game
```
/wps dump       then click/scroll through the English windows (60 s)
/reload         this SAVES everything to disk
```
The saved file is (account name will differ):
```
.../World of Warcraft/_forever_/WTF/Account/TUVEJANI/SavedVariables/wow_pa_svenska.lua
```
(NOT "WPSDB.lua" — the table inside is called WPSDB.)

### 2. Extract — make the tidy English list
From the repo root:
```bash
python3 tools/parse-uidump.py \
  ".../SavedVariables/wow_pa_svenska.lua" \
  -o translation/ui/dump-YYYY-MM-DD-en.tsv
```
The tool removes noise (already-translated texts, item tooltips, numbers)
and writes `id / area / english` rows.

### 3. Translate — by hand
Create `translation/ui/dump-YYYY-MM-DD-sv.tsv` with the SAME ids:
```
id	sv
001	Högre fiskekunskap ökar din chans att fånga fisk...
```
Rules that have actually saved us:
- **Copy the English exactly** from the en-file. Real traps we hit:
  double spaces after sentences ("Horde.  They"), "PvP" vs "PVP",
  invisible leading spaces (" Season 1").
- Numbers/colors in the text? Make a *format entry* instead:
  keep the markup, use `%s` where the numbers go:
  `ui["Next Rewards at Rank %s"] = "Nästa belöningar vid grad %s"`
- Glossary first (`translation/glossary-core.tsv`), du-form, "raid"
  stays "raid". Style rules: `translation/PROMPT-translation.md`.

### 4. Apply + check
Add the entries to `Data/UiExtra.lua` (put a dated comment on top). NEVER edit
`Data/Ui.lua` — it is generated and gets overwritten.
```bash
lua5.1 tools/check-ui-translation.lua \
  translation/ui/dump-YYYY-MM-DD-en.tsv translation/ui/dump-YYYY-MM-DD-sv.tsv
```
`RESULTAT: OK` proves every Swedish line is actually produced by the
current tables (catches typos, gaps, wrong markup). Also:
```bash
lua5.1 -e "assert(loadfile('Data/UiExtra.lua')); print('SYNTAX OK')"
python3 -m unittest discover -s tests
```

### 5. Deploy — copy to the game
```bash
cp Data/UiExtra.lua \
  ".../World of Warcraft/_forever_/Interface/AddOns/wow_pa_svenska/Data/"
```
(also copy `UI.lua`/`Options.lua` if you changed code), then `/reload`
in the game. Sanity check: run `/wps dump` once more — it should now
find ~0 new texts. Anything left: start again at step 1.

## Where things live

| file | what it is |
|---|---|
| `Data/UiExtra.lua` | hand-maintained UI translations (THIS is where entries go) |
| `Data/Ui.lua` | generated base list — do not edit |
| `UI.lua`, `Options.lua` | the swapping engine + `/wps dump` command |
| `translation/ui/dump-*.tsv` | capture pairs (english / swedish) per round |
| `translation/ui/UI-PLAN-2026-11-15.md` | the full analysis + history |
| `tools/parse-uidump.py` | dump file → english list |
| `tools/check-ui-translation.lua` | your quality gate |

## The easy way

Do only step 1 and hand the `wow_pa_svenska.lua` file (or screenshots)
to the translation agent — steps 2–5 run as shown here and the result
gets reviewed before it is copied into the game.
