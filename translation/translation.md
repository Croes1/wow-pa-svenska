# translation/translation.md — historisk logg från piloten

> Läs som historia (vad som gick fel och hur det lagades). Aktuell arbetsgång:
> `translation/PIPELINE.md` — inga API-anrop; agenten i VS Code-chatten
> översätter själv.

Fixed — and proven. Here's what happened and where you are now:
Fixed — and proven. Here's what happened and where you are now:

## What Gemma did wrong (and the fix)

On the last row (1160, "Test of Lore") Gemma wrote only **4 columns** — it forgot the two trailing *empty* columns (progress, reward) that every row must have. No words were wrong anywhere: the checker re-glues the 5 text fields and compares byte-for-byte against the original, and after adding the two missing empty fields it passes for all 10 rows:

```
kalla: 10 rader   segment: 10 rader   jamforda: 10
ruttade till granskning: 1 -> translation/batches/review/quests-batch-01-en-review.tsv
RESULTAT: OK - samtliga segment bygger samman till kallan
```

The 1 row in the review file is **expected** — it's quest 93429, the fragment we knew about (no title/objectives were ever collected for it). Gemma put its text in the *description* field, which is reasonable; a human confirms the final placement later. For this test: **translate it too** — the Swedish text is identical no matter which field it ends up in, and the merge step (a later, separately reviewed task) handles where it goes.

## Do this now — the translation test

1. **New Gemma chat** (temperature 0.2 if you can set it).
2. Paste the **TASK B block** from `translation/PROMPT-GEMMA.md` (everything inside the first ` ```text ` fence under "## TASK B"), unchanged.
3. Below it, paste **the whole file** `translation/glossary-core.tsv` (that's the word list — it now says `Rogue = Skurk`).
4. Below that, paste **all 10 lines** of `translation/segmented/quests-batch-01-en-segmented.tsv` (no header line — the file starts directly with `568...`). Copy from a real text editor like VS Code, **not** a wrapped terminal window, so the TAB characters survive the clipboard.
5. Save Gemma's reply as `translation/out/quests-batch-01-sv.tsv` (plain text, no markdown fences — if Gemma adds ``` lines, delete them).
6. Check it:
   ```
   python3 tools/validate-batch.py translation/batches/quests-batch-01.tsv translation/out/quests-batch-01-sv.tsv quests
   ```

**Expected result:** `RESULTAT: OK (några varningar)` — warnings you may see and should *not* panic about:
- `93429: titeln ar tom` → correct, the quest has no title.
- Warnings about unchanged English in a field → means Gemma kept English somewhere; those rows are the ones to eyeball before merging.

If you get `FEL:` lines (count-mismatched `$B/$b` tokens, missing/duplicate ids, wrong column counts), paste the listed **ids only** back to Gemma with the TASK B block again — not the whole batch.

**Status 2026-11-15:** the API-runner idea is dead and buried. `tools/run-gemma.py`,
its tests, the API key (`.env`) and the /tmp queue scripts were removed from
the repo, and translation APIs are now banned outright — any AI is not
allowed, whatever the brand (root `AGENTS.md`,
`translation/PIPELINE.md`). Every batch — including this one — is done the new
way: the agent segments and translates itself in the VS Code chat, and the
offline checkers decide.