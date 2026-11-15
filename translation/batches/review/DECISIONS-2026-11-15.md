# Beslut — fältplacering & översättning av de 5 hoppade raderna (2026-11-15)

De här fem raderna gick aldrig via något API den här omgången: segmenteringen
(Task A) och översättningen (Task B) är gjorda för hand och kontrollerade med
samma offline-verktyg (`verify-segmentation.py`, `validate-batch.py` — inga
nätverksanrop). Grundprinciper: segmenten bygger om källradens brödtext byte
för byte; tomma fält förblir tomma; platshållare/markup ($B, $2oa) kopieras
orört; namn översätts enligt ordlista och skickad data (se nedan).

Obs: `verify-segmentation.py` skriver om review-filerna vid varje körning
(batch-03: 7 rader, batch-07: 5 rader — samtliga rader med tom titel är
automatiskt routade). Besluten per rad ligger därför här i stället.

| id | batch | placering | beslut & motivation |
|----|-------|-----------|---------------------|
| 79677 | 03 | titel tom, all text i objectives-fältet | Fragmentpost i ogrardialekt utan titel. Följer batchens etablerade mönster (97287/79361/97196/97200/94532/98069: titel tom, text i första icke-tomma fältet). Svenskan bevarar den torra ogrartonen ("inte riktigt en logistikkille"). |
| 586 | 07 | titel + objectives + description | Riktig uppdragsstruktur: "Speaking with Gan'zulah" är titel; kill-/bring-raderna är objectives; allt från `<The head of Gan'zulah speaks.>` är description (anmärkningen inleder uppdragshistorien). Ingen progress/reward i källan. |
| 5763 | 07 | titel + objectives + description | Vanlig uppdragspost: "Hunting in Stranglethorn" titel, "Bring Roon's Kodo Horn ..." objectives, resten description. |
| 94221 | 07 | titel + objectives + description | Hantverksorder, identisk mall med 94239 ("Hantverksorder: Fina läderbyxor", redan grön i batch-10). `<Penned in faded ink ...>`-noten är description. |
| 98248 | 07 | titel tom, all text i description-fältet | Bokstavlig svans av en writ-note (källraden slutar med ett överblivet `>`). Naturligt hem är description (jfr 93429 i batch-01: narrativt fragment → description). Det är en egen (kapad) källpost, inte en fortsättning som ska läsas in i 94221. |

## Birega: befintlig felrad lagad

- **id 1147 (batch-03, svensk fil)**: raden tappade en `$B`-token
  ("...kröp upp ifrån.$B$Jag antar..." → "...$B$BJag antar..."). Det är därför
  batch-03 aldrig varit grön i validern (`platshallare saknas: $B x1 /
  platshallare tillagda: $Jag x1`). Endast markeringen återställd — inga ord
  ändrade. Efter lagningen: `RESULTAT: OK (7 varningar)`.

## Terminologi (ur ordlista + skickad data)

- Craftsman's Writ = **Hantverksorder** (94239 "Hantverksorder: Fina läderbyxor")
- Golden Rod = **Guldstav** (stavfamiljen i skickad data: Kopparstav, Runristad kopparstav, Silverstav)
- Stranglethorn = **Strypetörnsdalen**, Desolace = **Ödelandet** (ordlistan)
- Grom'gol Base Camp = **Grom'gol-baslägret** (jfr "i Grom'gol" i 571)
- Roon's Kodo Horn = **Roons kodohorn** (jfr "Kodoben", "Kodojägarens hosor")
- Skullsplitter-jägare/huvudjägare/berserker — stamnamnet behålls, rangorden
  översätts (samma mönster som "Boulderfist-ograr"/"Boulderfist-ordningsvakter"
  i 676); "the Skullsplitters" = "Skullsplitterna"
- Ana'thek the Cruel = **Ana'thek den Grymme** (personnamn orört);
  Broken och shattered armor = **sönderslagna rustningen** (samma föremål båda fallen)
- Bubbling Cauldron = **den bubblande kitteln** (gameobject saknas i skickad data — fri översättning)

## Sammanfogning (MERGE) — gjord 2026-11-15

Ovanstående placeringar är nu sammanfogade och verifierade:
`tools/merge-translation.py` skapade `Data/QuestExtra.lua` /
`Data/NpcExtra.lua` (tilläggsfiler — `Data/*.lua` rördes inte) som laddas via
`wow_pa_svenska.toc`. Utfallet: 79677 → o-fältet, 586/5763/94221 kompletta
(t+o+d), 98248 → d-fältet; lua5.1-syntakstest + runtime-check (quest 1 893,
npc 1 660) grönt. Spårrader (`l`) saknas fortfarande — de förblir engelska.
`$2oa` skickas orörd (se "Öppna runtime-frågor" i PROMPT-GEMMA.md). Vid nästa
omgång gäller samma tumregel som alltid: `/wps fel` är domare.