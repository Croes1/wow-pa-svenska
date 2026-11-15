# Promptblock för översättningsagenten – två separata steg (A: segmentera, B: översätt)

> The loop from newly collected data to finished `-sv.tsv` files is
> documented in `translation/PIPELINE.md` (in English). This file contains the
> TASK blocks those steps run.
>
> **INGA API-ANROP:** agenten i VS Code-chatten utför TASK A och TASK B **själv**
> i samtalet och skriver filerna direkt. Anropa aldrig någon extern AI-tjänst,
> modell eller översättnings-API, inga HTTP-endpoints (den tidigare API-köraren
> `tools/run-gemma.py` och nyckeln i `.env` är borttagna 2026-11-15).
> Filnamnet `-GEMMA` är historiskt.

Arbeta alltid i den här ordningen; segmenteringen (A) och översättningen (B)
är två fristående steg, varje steg med egen fil och egen kontroll. **Agenten i
VS Code-chatten är utföraren**: läs TASK-blocket, följ det ordagrant, skriv
resultatet till filen och kör kontrollen. "Klistra in"-vändningen nedan är den
manuella (läs: mänskliga) varianten av samma sak:

1. **Steg A – segmentera engelskan.** Följ TASK A-blocket (orubbligt) för
   uppdragsbatchen utan rubrikraden. Spara resultatet som
   `translation/segmented/quests-batch-XX-en-segmented.tsv`.
   Kontrollera med
   `python3 tools/verify-segmentation.py translation/batches/quests-batch-XX.tsv translation/segmented/quests-batch-XX-en-segmented.tsv`.
   FEL => segmenten bygger inte om källtexten; gör om bara de id:en (utan att
   hitta på text). Rader som routas till
   `translation/batches/review/quests-batch-XX-en-review.tsv`
   (tom titel, fragment) placeras för hand innan de går vidare — beslutet
   dokumenteras, jfr `translation/batches/review/DECISIONS-2026-11-15.md`.
2. **Steg B – översätt till svenska.** Följ TASK B-blocket och ordlistan
   `translation/glossary-core.tsv` mot den *segmenterade* filen från steg A
   (utan rubrikraden). Spara svaret som
   `translation/out/quests-batch-XX-sv.tsv`. Kontrollera med
   `python3 tools/validate-batch.py translation/batches/quests-batch-XX.tsv translation/out/quests-batch-XX-sv.tsv quests`.
3. **NPC-namn:** TASK B/NPC-variantblocket mot `npcs-batch-XX.tsv` (utan
   rubrik), ut som `translation/out/npcs-batch-XX-sv.tsv`, kontroll med
   `... npcs` i stället för `quests`.
4. **Repetera bara misslyckade id** när kontrollen rapporterar FEL, inte
   hela omgången. Håll filerna hela och i batchordning innan du kör
   kontrollen mot hela batchen.

## Riktlinjer för agenten som gör stegen i chatten

- **Ett batch-steg i taget**: steg A för en batch, verifieraren, granskning av
  review-rader, steg B, validern — innan nästa batch påbörjas. Saknas bara
  enskilda id:n gör du om exakt de raderna, inte hela filen.
- **Ordlistan är obligatorisk** i varje steg B: läs `translation/glossary-core.tsv`
  (sök vid behov i `translation/glossary-all.tsv`) innan du skriver svenska.
- **Kontexten ska vara ren**: räkna platshållarna ($B/$b-par, #/#, %s, $2oa …)
  i källan och i din svenska innan filen skrivs; validern räknar dem per rad
  och godkänner annars inte batchen.
- Spara dotterfiler under `translation/segmented/` och `translation/out/` med
  samma nummer som batchen (t.ex. `-01-`), så blir hopkopplingen enkel.

---

## TASK A – segmentera engelsk questtext (klistra in orubbligt)

```text
You split World of Warcraft (classic era) quest text that is stored as ONE
string: title, objectives, description, progress text and reward dialogue
glued together with no delimiter. You do NOT translate - you only split.

INPUT: TSV lines: id<TAB>body
A single leading space often precedes the title. Some records are fragments:
they start mid-sentence, with '<', or with a $-token like $C, and have no
title at all.

TASK: for each input row, output exactly one row:
id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward

- title       = the quest name shown above the text
- objectives  = the "X wants you to ...", "Bring N ... to Y" summary line
- description = the longer story/dialogue text behind it
- progress    = the mid-quest hand-in line if one is present, else empty
- reward      = the turn-in dialogue granting the reward, else empty

RULES
1. The five fields, concatenated in this order, must reproduce the body
   exactly, except that whitespace at the very start or very end of the body
   may be dropped. Add nothing, drop nothing, reorder nothing; do not touch
   spaces inside the text and do not split words.
2. A field that does not exist stays EMPTY. Never invent a title,
   objectives, progress or reward text: if the body has no title (fragment),
   leave title empty and keep the text where it naturally falls.
3. If you cannot locate a boundary, keep the text in the earlier field
   rather than guessing a mid-sentence break.
4. Game tokens ($B, $b, $c, $C, $n, $N, $r, $R, $2oa and friends) stay
   attached to their surrounding text, byte for byte.
5. OUTPUT: only the TSV rows, same ids and order, no markdown, no
   numbering, no commentary, no blank lines.
```

### Verifierat exempel (rad 3341, ur `translation/batches/quests-batch-01.tsv`)

Inmatning (fält separeras med TAB):

	3341	Bring the EndAndrew Brownell wants you to kill Amnennar the Coldbringer and return his skull.In the Barrens lies a horrid mess of tangled vines called Razorfen Downs. While our first observations of this place revealed little threat, our recent findings are much more serious...$B$BThe quilboar of Razorfen Downs have aligned themselves with the Scourge. A Lich named Amnennar the Coldbringer rules them now, using the power of his massive consciousness to control their every move.$B$BAmnennar has a direct telepathic link to Ner'zhul; we must sever this bond, $n. An end must come to the Coldbringer.

Korrekt utmatning:

	3341	Bring the End	Andrew Brownell wants you to kill Amnennar the Coldbringer and return his skull.	In the Barrens lies a horrid mess of tangled vines called Razorfen Downs. While our first observations of this place revealed little threat, our recent findings are much more serious...$B$BThe quilboar of Razorfen Downs have aligned themselves with the Scourge. A Lich named Amnennar the Coldbringer rules them now, using the power of his massive consciousness to control their every move.$B$BAmnennar has a direct telepathic link to Ner'zhul; we must sever this bond, $n. An end must come to the Coldbringer.		

(titel, mål, beskrivning – sedan två tomma fält.) De fem fälten sammansatta
blir exakt källtexten; det är det `tools/verify-segmentation.py` bevisar.

### Fragmentpost (rad 98070, ur `batches/quests-batch-14.tsv`)

Källan börjar mitt i en mening och saknar titel. Korrekt utmatning lämnar
titel och mål tomma och stoppar texten i ett av de bakre fälten; raden
skickas därefter till `translation/batches/review/quests-batch-14-en-review.tsv` av
kontrollen och översätts inte vidare förrän en människa med källtexten i
spelet avgjort vilken kolumn texten tillhör.

---

## TASK B – översätt segmenterad engelska till svenska (klistra in orubbligt)

```text
You are a professional game localizer translating World of Warcraft (classic
era) quest text from English into Swedish for the translation addon
"Wow på Svenska".

INPUT: TSV rows id<TAB>title<TAB>objectives<TAB>description<TAB>progress<TAB>reward
(English, already segmented). OUTPUT: one row per input row with the SAME
columns, translated to Swedish. A field that is empty in English stays
empty in Swedish.

RULES
1. Follow the attached GLOSSARY (table, english, swedish) exactly; it matches
   the shipped game data (Rogue = Skurk, Rogues' Quarter = Skurkarnas
   kvarter). If a glossary entry ever disagrees with shipped data for the
   same proper noun, prefer the shipped form and tell the maintainer.
2. NEVER translate, reorder or remove game tokens; copy byte for byte:
   $N $n $C $c $R $r $B $b, gender switches $Gman:kvinna; and $g...;,
   spell tokens like $s1 $d $t1 ${$m2$*$<frostdamage>}, the counter #/#,
   format specifiers %s %d, and colour/link markup |cffrrggbb...|r and
   |H...|h[...]|h. Unknown tokens such as $2oa are copied as they are -
   they belong to the game client, not to you. Do not ADD or DROP tokens:
   the validator counts them per row and rejects the batch on any change.
3. Names:
   - Personal names (a character: "Doctor Marsh", "Karu", "Mennet Carkad")
     stay in English. A rank in front of the name may be translated
     ("Guard Thomas" -> "vakt Thomas"), the personal name itself never is.
   - Descriptive names (a creature or type: "Timber Wolf", "Scarlet
     Crusader") are translated into natural Swedish compounds following the
     glossary; shipped examples: Forest Spider -> Skogsspindel,
     Harvest Golem -> Skördegolem, Defias Night Blade -> Defiasnattklinga.
4. The word Rogue is always "Skurk": the player class, a villain person, the
   Undercity district (Rogues' Quarter = Skurkarnas kvarter) and mob names
   (Syndicate Rogue = Syndikatskurk). Two shipped exceptions: the creature
   word "scalawag" is "skälm", and the harpy "Roguefeather" keeps its
   shipped Swedish form ("Bloodfury Roguefeather" = "Blodvredesskälmfjäder").
   If you are unsure which case you have, keep the English word and let the
   review row decide - do not guess.
5. Style: address the player as "du" (never "ni"); classic quest-giver
   voice, but NATURAL Swedish first - do not stack archaisms ("eder",
   "sannerligen") unless the English is already formal-epic. Ellipsis is
   " ...", straight quotation marks, decimal comma, and a space before
   percent the way shipped data does it: "$s1 %".
6. OUTPUT: only the TSV rows, same ids and row order, exactly six columns,
   no markdown, no numbering, no commentary, no blank lines. If you cannot
   translate a field with confidence, keep the ENGLISH text in that field;
   never invent Swedish and never leave a whole row empty.
```

Rättelser jämfört med den gamla versionen av den här filen:

- `Ironforge=Jarnsmedjan`, `Darkshire=Morkby`, `Ratchet=Sparrhake` m.fl. hade
  tappat å, ä, ö. Riktiga stavningar enligt ordlistan: **Järnsmedjan,
  Mörkby, Spärrhake, Stormvind, Stormvinds stad, Elwynnskogen,
  Skymningsskogen, Kargmarkerna (The Barrens), Bytesbukten (Booty Bay),
  Understaden (Undercity), Dunderklippan (Thunder Bluff), Våtmarkerna
  (Wetlands), Tirisfalgläntorna (Tirisfal Glades)**.
- Fallback-raden "skriv hela engelska brödtexten i titelfältet" är borttagen.
  Översättning bygger på fält från segmenteringssteget; en rad man litar inte
  på behåller sin engelska text, och kontrollen/granskningen plockar bort den.
- Ordlistorna är omexporterade från källan (`Data/Glossary.lua` via
  `tools/export-glossary.lua`), så alla Rogue-rader lyder **Skurk**: 2 rader i
  `glossary-core.tsv` (Rogue, Rogues' Quarter -> Skurkarnas kvarter) och 55
  rader i `glossary-all.tsv` (spells, items, qtext). Undantag enligt skickad
  data: harpan "Roguefeather" = "Blodvredesskälmfjäder".

### Verifierade exempel (hämtade ur skickad data, inte påhittade)

Båda raderna nedan står ordagrant i addonen i dag (Data/Spell.lua respektive
Data/Glossary.lua). Notera token-mönstret `$s1%` -> `$s1 %` i svenska.

| engelska (in) | svenska (ut, skickad) |
|---|---|
| `Launches a bolt of frost at the enemy, causing ${$m2$*$<frostdamage>} to ${$M2*$<frostdamage>}  Frost damage and slowing movement speed by $s1% for $d.` | `Skjuter en frostbult mot fienden. Bulten orsakar ${$m2$*$<frostdamage>} till ${$M2*$<frostdamage>} frostskada och saktar ned förflyttningshastigheten med $s1 % i $d.` |
| `Bring 8 Torn Murloc Fins to Guard Thomas at the east Elwynn bridge.` | `Ta med 8 sönderrivna murlocfenor till vakt Thomas vid bron i östra Elwynn.` |

NPC-namn (alla fyra finns i skickad data i Data/Glossary.lua och visar regeln):

| engelska | svenska | typ |
|---|---|---|
| `Forest Lurker` | `Skogslurare` | beskrivande -> översätts |
| `Forlorn Spirit` | `Övergiven ande` | beskrivande -> översätts |
| `Deputy Feldon` | `Konstapel Feldon` | person -> bara rangen översätts |
| `Demnul Farmountain` | `Demnul Farmountain` | rent personnamn -> oförändrat |

### Saknade `l`-rader (täckningsbegränsning – viktigt!)

I skickad data har varje uppdrag ofta en `l={...}`-lista: de objektivrader som
syns i uppdragsloggen/spåraren (t.ex. `"#/# Garricks huvud"`). Texterna till
dem finns INTE i de batcher vi skickar nu: källcachen innehåller bara
titel/mål/beskrivning/progress/belöning. Därför:

- Modellen ska ALDRIG hitta på `l`-rader eller lista dem.
- Uppdrag som läggs in nu får tills vidare engelska spårrader i spelet –
  saknad översättning betyder engelska kvar, inget går sönder.
- Det är en täckningsbegränsning i dataflödet, inte ett modellfel; ett
  framtida steg kan hämta objektivraderna ur speldatabasen.

---

## NPC-variant av TASK B (klistra in i stället för questreglerna)

```text
Same system as before; replace the TASK/RULES with:

INPUT: TSV lines id<TAB>name<TAB>title
OUTPUT: exactly one row per line: id<TAB>swedish-name

- The title column is reference only; it is NOT part of the output.
- Personal names (an NPC who is a character) stay in English. A rank in
  front of a personal name may be translated ("Deputy Feldon" ->
  "Konstapel Feldon"); shipped data keeps "Demnul Farmountain" as is.
- Descriptive names (creatures, professions, unit types) become natural
  Swedish compounds following the glossary; shipped examples:
  Forest Spider -> Skogsspindel, Forest Lurker -> Skogslurare,
  Forlorn Spirit -> Övergiven ande, Defias Pillager -> Defiasplundrare.
- Follow the glossary first; names missing from it may stay English.
- Output only TSV rows, same ids and order, no commentary, no blank lines.
  If a name cannot be translated with confidence, keep the English name.
```

(Påminnelse: validern flaggar oförändrade namn som VARNING – det är avsett,
personnamn ska stå orörda. Skriv ändå ut dem, så blir hopslagningen enkel.)

---

## Automatiserad körning via API — BORTTAGET

Detta avsnitt beskrev förr automatisk körning mot ett externt modell-API med
`tools/run-gemma.py`. Det är taget bort 2026-11-15: **inga API-anrop görs
från detta repo** — ingen AI är tillåten: inga AI-tjänster, inga modell-API:er,
inga HTTP-endpoints. Agenten i VS Code-chatten gör segmenteringen och
översättningen själv enligt TASK-blocken ovan, skriver TSV-filerna och kör
de offline-kontroller som finns kvar i `tools/` (verify-segmentation,
validate-batch, fix-empty-columns — alla helt nätverksfria). API-köraren,
dess tester, nyckeln i `.env` och köskripten i /tmp är borttagna och ska
inte återskapas.

## Kontroller, granskning och vad de bevisar

```bash
# steg A - engelsk segmentering (partition av källtexten)
python3 tools/verify-segmentation.py \
    translation/batches/quests-batch-XX.tsv \
    translation/segmented/quests-batch-XX-en-segmented.tsv

# steg B - svensk översättning (id-sekvens, kolumner, token-mängder)
python3 tools/validate-batch.py \
    translation/batches/quests-batch-XX.tsv \
    translation/out/quests-batch-XX-sv.tsv quests     # eller npcs
```

En vanlig feltyp (historiskt hos Gemma) ar att tappa de tomma slutkolumnerna
(progress/reward); validern rapporterar da "4 kolumner (vantade 6)" for raden.
Det lagas sa har - verktyget fyller ENDAST pa kolumner som ar tomma aven i den
engelska referensen; ar engelskan fyllt dar rapporteras FEL och raden skrivs
om av agenten. Kor validern en gang till efterat:

```bash
python3 tools/fix-empty-columns.py \
    translation/segmented/quests-batch-XX-en-segmented.tsv \
    translation/out/quests-batch-XX-sv.tsv
```

- Verifieraren bevisar att segmenten **sammansatta** blir källtexten (minus
  inledande/avslutande mellanslag). Den kan inte säga att texten hamnat i
  RÄTT kolumn - därför finns granskningsfilen.
- Validern bevisar att strukturen stämmer: samma id:n i samma ordning,
  rätt kolumnantal, och att varje `$`-token, `#/#`, `%s`, färg-/länk-markup
  förekommer LIKA många gånger som i källan - varken saknade, extra eller
  omräknade.
- Ingen av kontrollerna säger att svenska är bra. Kvaliteten avgörs av
  mänsklig granskning och `/wps fel`-rapporter från spelet; kontrollerna
  ser bara till att ingen text tappas och att ingen markup förändras.

## Öppna runtime-frågor (obesvarade - inget har ändrats i koden)

- `$2oa` i "Craftsman's Writ"-uppdragen (t.ex. 94220): kopieras av validern
  som en token, men hur WoW-klienten tolkar den är obekräftad. Inget i
  addonet hanterar `$2oa` i dag; tokenen skickas oförändrad tills den kan
  provas i spelet.
- Kolumnordningen vid framtida sammanslagning (QuestExtra.lua) ska motsvara
  Data/Quest.lua: `t, o, d, p, c` (title, objectives, description, progress,
  completion). Det arbetet ingår inte i den här ändringen.
