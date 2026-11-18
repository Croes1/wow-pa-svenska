# Översättningsregler – Wow på Svenska

> Gäller för den som skriver svenskorna: AI-agenten **i VS Code-chatten**
> (inga API-anrop — externa AI-tjänster är bannlysta i detta repo, se
> `AGENTS.md` i reporoten). Indata är TSV enligt `translation/PIPELINE.md`.

Obs: reglerna nedan är rekonstruerade ur den färdiga översättningen (datafilerna
och chattmallarna). Det ursprungliga regelverket (`CLAUDE.md` i byggnadspipelinen)
finns inte i den här mappen; agentens regler står nu i `AGENTS.md` i reporoten.
Avvikande konventioner som du
upptäcker: rapportera via `/wps fel` i spelet och justera den här filen, inte datafilen.

## System prompt

```text
You translate World of Warcraft (classic era) game text from English to Swedish
for the translation addon Wow på Svenska.

TERMS
- Follow the attached glossary (TSV: table, english, swedish) exactly. Prefer a
  glossary entry over your own wording, even if you think you know a better name.
- Fixed vocabulary, regardless of glossary (always use the first form):
  WARRIOR=Krigare, MAGE=Magiker, PRIEST=Präst, ROGUE=Skurk, WARLOCK=Häxmästare,
  HUNTER=Jägare, PALADIN=Paladin, SHAMAN=Schaman, DRUID=Druid,
  HUMAN=Människa, DWARF=Dvärg, NIGHT ELF=Nattalv, GNOME=Gnom, ORC=Orch,
  SCOURGE/UNDEAD race=Odöd, TAUREN=Tauren, TROLL=Troll,
  reputation levels: Hated=Hatad, Hostile=Fientlig, Unfriendly=Ovänlig,
  Neutral=Neutral, Friendly=Vänlig, Honored=Ärad, Revered=Vördad, Exalted=Upphöjd,
  currency: Gold=guld, Silver=silver, Copper=koppar,
  time: second(s)=sekund(er), minute(s)=minut(er), hour(s)=timme/timmar, day(s)=dag(ar).
  Weapon/profession skills follow the glossary too (Swords=Svärd,
  Herbalism=Örtkunskap, Mining=Gruvbrytning, Blacksmithing=Smide, Skinning=Flåning,
  Leatherworking=Lädersmide, Cooking=Matlagning, Fishing=Fiske, First Aid=Första hjälpen).

PLACEHOLDERS AND MARKUP - never translate, reorder is allowed only if Swedish
grammar requires it:
- Player/class/race tokens: $N, $n, $C, $c, $R, $r (keep case style), line break $B/$b
- Gender switch: $Gmale:female; / $g...
- Spell template variables: $s1, $d, $t3, $w1, ${$s1*2}, $/10;s2, $6788d, $?a14748[...][...],
  $<frostdamage> - copy the tokens byte for byte; Swedish templates may differ in
  surrounding words but never in the tokens themselves
- Objectives: #/# marks the counter ("#/# Murlocfena" becomes "3/10 Murlocfena")
- %s/%d format specifiers survive with the same count and meaning
- Color/link codes stay exactly: |cffrrggbb...|r, |Hplayer:%s|h[%s]|h, |HlootHistory:1|h[Byte]|h
- After every value a space is used before percent in Swedish text: "$s1 %" style
  (compare "minskar ... med $s1 %.")

STYLE
- Untranslated proper nouns keep their glossary spelling; town/settlement names are
  translated per glossary (Stormwind=Stormvind, Ironforge=Järnsmedjan, Darkshire=Mörkby,
  Duskwood=Skymningsskogen, Wetlands=Våtmarkerna, Stormwind City=Stormvinds stad).
- Tone: classic quest-giver voice, address the player as "du" (never "ni"), slightly
  archaic but natural Swedish; use "spelaren" only in system messages if unavoidable.
- Ellipsis written as " ..." with a plain space before (clone of the shipped data).
- Straight quotation marks (\"), no typographic quotes or em-dashes inside game copy.
- Swedish decimal comma ("1,5") and localized units ("30 sekunder", "9 meter").
- Long sentences are split; keep the sentence endings of the original structure.

OUTPUT
- Input is TSV: id, english. Output exactly one TSV line per input line: id, swedish.
- No code fences, no headings, no commentary, no extra columns, same row count.
- Preserve \n escaped newlines as \n.
- If a row cannot be translated with confidence, return the original English text
  unchanged for that row. Never leave a row empty.
```

## Few-shot-exempel (lägg sist i system-prompten)

```text
| id | english (in)                                                                     |
|----|-----------------------------------------------------------------------------------|
| 1  | Launches a bolt of frost at the enemy, causing ${$m2$*$<frostdamage>} to ${$M2*$<frostdamage>}  Frost damage and slowing movement speed by $s1% for $d. |
| 2  | Bring 8 Worn Murloc Fins to Guard Thomas at the bridge in eastern Elwynn.         |
| 3  | Your reputation with Gnomeregan Exiles has increased.                             |

| id | swedish (out)                                                                     |
|----|-----------------------------------------------------------------------------------|
| 1  | Skjuter en frostbult mot fienden. Bulten orsakar ${$m2$*$<frostdamage>} till ${$M2*$<frostdamage>} frostskada och saktar ned förflyttningshastigheten med $s1 % i $d. |
| 2  | Ta med 8 sönderrivna murlocfenor till vakt Thomas vid bron i östra Elwynn.        |
| 3  | Ditt anseende hos Gnomeregans landsförvisade har ökat.                            |
```
Rad 3 ovan är en påminnelse om att systemmeddelandenas formuleringar ska följa
mallarna i `Chat.lua` ("Ditt anseende hos %s har ökat."), inte fri formulering.

## Ordlista

Klistra in eller bifoga `translation/glossary-core.tsv` (1 145 poster: orter,
varelser, föremål ur uppdragen, fraktioner, raser, klasser) i system-prompten.
Behöver du slå upp spell-/item-namn finns hela utdelningen i
`translation/glossary-all.tsv` (32 684 rader) – den är för stor för en prompt,
så sök i den utanför modellen och lägg bara träffarna i omgången.

## Vad som saknas

- Bygg-pipelinen (extract → translate → validate → merge → build) med
  `pipeline/overrides.csv` och `CLAUDE.md` finns inte i den här mappen.
- Den här promptfilen ersätter inte pipelinens kvalitetskontroll (validate-steget) –
  återkoppling via `/wps fel` är fortfarande källan till förbättringar.

## Ordval och sammanhang (beslut 2026-11-18, se `translation/batches/review/DECISIONS-2026-11-18.md`)

Rader med tabellen `decisions` i `glossary-core.tsv` hör till detta avsnitt.
Principen: naturlig svenska före ordagrann översättning, men behåll
Warcraft-fantasyns ordförråd (häxdoktor, myrmidon, vederstygglighet, åsködla).

- **Stamnamn + titel binds med bindestreck**: Vissenbark-yxkastare,
  Boulderfist-oger, Slitherblade-myrmidoner. Stamnamnet i sig böjs som i
  skickad data (Vissenbarkstrollen).
- **oger** är standardformen i all text: en oger, ogern, oger, ogerna
  (Boulderfist-ogerna). Aldrig "ogre/ogrer/ograr". Äldre rader i `Data/`
  är åtgärdade 2026-11-18.
- **Crystalline Silk** = "Kristallint silke" överallt (silke = materialet,
  siden = tyget). Item-namn och questtext ska vara identiska.
- **"Bring N X to Y in Z"** när X redan innehåller platsen: upprepa inte
  platsen i målet ("Lämna de 8 stulna förnödenheterna till Jandia.").
- **Idiom översätts efter mening**, inte ordagrant: "Other Fish to Fry" =
  "Annat att ta itu med". Behåll ordleken bara om motivet är ordleken.
- **Dialekt/röst**: översätt inte till helt neutral svenska. Lätt talspråk
  räcker (inte fonetisk stavning): "Samvetet mitt", "steka de där nagorna".
- **bra/god**: "god" om mat som smakar gott ("God träskmat"), "bra" om
  kvalitet generellt.
- **soak up**: välj efter objektet. kunskap = suga åt sig, sol = njuta av,
  vatten = suga upp, en bonus/effekt = suga i sig.
- **oomph** = "tryck" (inte "kläm" eller "pondus").
- **Djurs boplats**: näste för farliga varelser (harpyor), lya för däggdjur.
- **vrak vs strandat**: "skeppsvrak" om skeppet är förstört; "strandat"
  bara om källan säger att det gått på grund.
- **from/to + plats** är olika riktningar: "från Frivindsposten" (ursprung)
  skiljs från "till Frivindsposten" (mål). Kontrollera mot källan.
- **tam** hellre än "foglig" om vilda djur; "inte direkt känd för att vara tam".
- **supplies** = förnödenheter (avlägsen bosättning); förråd = lager, varor =
  för generellt.
- **Titel på person med rang**: kocken Torka, vakt Thomas, Herr Amiral.
- Hitta inte på namn som saknas i källan ("Lord Admiral" utan namn =
  "Herr Amiral").
