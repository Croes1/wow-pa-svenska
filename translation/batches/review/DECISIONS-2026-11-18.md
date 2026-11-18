# Beslut — ordval i quests-batch-01 (2026-11-18)

Underlag: granskning av maintainern. Allmänna regler står i
`translation/PROMPT-translation.md` ("Ordval och sammanhang"), enskilda termer
som rader i `translation/glossary-core.tsv` (tabell `decisions`).

| id | före | efter |
|----|------|-------|
| 5501 | Är det en deal? | Är vi överens? |
| 95508 | Lordamiralen | Herr Amiral |
| 677 | Vissenbarksyxkastare / Boulderfist-ogrerna / är tjocka av blod | Vissenbark-yxkastare / Boulderfist-ogerna / dryper av blod |
| 96260 | Dysterhöjdsspinnare / kristallint siden | Dysterhöjdens spinnare / kristallint silke |
| 6143 | Andra fiskar att steka / Ranazjar Isle / det strandade skeppet vid kusten härifrån / Mitt samvete / steker dem nagor | Annat att ta itu med / Ranazjarön / skeppsvraket utanför kusten längre norrut / Samvetet mitt / steker de där nagorna |
| 97985 | inte känd för att vara foglig | inte direkt känd för att vara tam |
| 96046 | lägerföremål / dra nytta av den extra "kläm" | lägerutrustning / suga i sig det extra "trycket" |
| 98069 | Stulna förnödenheter från Frivind | Stulna förnödenheter från Frivindsposten |
| 1218 | Bra träskmat | God träskmat |

## Uppföljningsbeslut (samma dag)

- **Kristallint siden -> Kristallint silke** överallt: `Data/Item.lua`,
  `Data/Glossary.lua`, `translation/glossary-all.tsv` (1 rad vardera).
  Silke = materialet, siden = tyget; item-namn och questtext ska vara lika.
- **98069**: målet är nu "Lämna de 8 stulna förnödenheterna till Jandia."
  (talet 8 behållet från källan; Frivindsposten upprepas inte). Föremålsnamnet
  är "Stulna förnödenheter från Frivindsposten".
- **oger standardiseras** (en oger, ogern, oger, ogerna): alla äldre former
  (ograr/ograrna/ogrer/ogrerna) i `Data/Quest.lua` (10), `Data/QuestExtra.lua`
  (5) och `Data/Item.lua` (1, "gordokogernas bojor") är ersatta. Ingen annan
  text rördes; lua5.1-syntaxkontroll grön.
- Obs: `Data/*.lua` är i filhuvudet markerade som genererade av
  `pipeline/vak.py` (finns inte i repot). Görs en omgenerering från den
  källan måste samma tre ändringar göras där, annars återkommer de gamla formerna.

## Öppna punkter

- bab.la gav 403 (blockerad för automatiska anrop); inga uppslag därifrån.

## Omgång 2026-11-18 — quests-batch-02..31, npcs-batch-01..26, pagetext 01..07, gameobjects 01..07

Allt skrivet till `translation/out/` och `translation/segmented/`; **inget i `Data/` rördes av den här omgången** (utöver de tre ändringarna ovan).
Kontroller: verify-segmentation OK för alla 31 questbatcher; validate-batch OK för alla quest-, NPC- och page-text-batcher.
Game objects: se "Gameobjects" nedan.

### Redan levererade id:n i `Data/QuestExtra.lua` / `Data/NpcExtra.lua`
`select-untranslated.py` jämför bara mot `Quest.lua`/`Npc.lua`, så batcherna innehåller id:n som redan finns i `*Extra.lua`.
- **NPC:** 1136 av 3888 rader fanns redan i `NpcExtra.lua`; de återanvänds oförändrade i `out/`.
- **Quests, återanvända oförändrade (komplett rad i QuestExtra, validerar mot källan)**, 55 id:n:
  5762 556 629 185 676 1049 1150 5386 2842 635 5763 596 552 190 639 1113 553 1048 550 1109 672 1361 533 6521 1151 6142 671 8551 573 586 2932 1205 3341 2342 1107 1106 1160 518 705 605 1373 679 606 570 2418 709 1362 1112 1187 656 673 680 595 1182 1482
- **Quests, ofullständig rad i QuestExtra (fragment) — ny fullständig översättning gjord**, 21 id:n (bör granskas mot befintlig fragmentrad innan sammanslagning):
  544 98070 86576 96774 96988 93225 93680 97265 96986 96063 97196 93429 79361 97287 94481 92519 97386 97539 95982 93663 95955
- **batch-01:** 6143, 97985, 98069 finns i QuestExtra med äldre ordval; batch-01-översättningen följer dina beslut ovan och skiljer sig därför från de levererade raderna.
  Sammanslagningen hoppar över id:n som redan finns — besluta om batch-01-orden ska ersätta de levererade.

### Nya ordval (se även tabellen `decisions` i `glossary-core.tsv`)
Venture Co. = Äventyrsbolaget(s) (även i questtext 201/213 — rättat); Tarnished = Fläckad; Broodmother = honummöder; Highland Strider/Thrasher = Höglandsstövare/-piskare;
Shadowmaw = Skuggkäft; mountaineer = bergsjägare; -hoof-efternamn följer skickad data (Bena Vinterhov → Tah/Nida/Komin/Mani Vinterhov).
Panther Mastery = Pantermästerskap (följer levererad rad 190); Tiger Mastery = Tigerbehärskning (levererad rad 185).

### Gissningar / ej i ordlista — rader att granska
Egennamn på platser/grupper saknade i ordlistan och översatta fritt: Thunder Axe-fästningen, Det vidriga revet (629), Mannorockulten, Ranazjarön, Roguefeather-lyan/-harpyor (rule 4: Roguefeather lämnat engelskt), Skrikkanjonen, Nattnätshålan, Träskljusherrgården/Mörkdimmegrottan (1206), Himmelsväktarplatån (96294), Viskande skogen/Shadowvale, Torrmustaschklyftan (642), Södra himlarnas plattform m.fl. i game objects.
Items utan ordlistepost: ivrets hjärtan (1113), Elementens essens (3911), raktyper som Höglandsköttlurpassare, Djungellurpassare, Dalaranframmanare/elementarslavar (545), titlar Höginkvisitor/Scharlakansröd befälhavare/hundmästare (1048, 1053).
NPC-/mobnamn med fri översättning: se `translation/out/npcs-batch-*-sv.tsv` (stamnamn behållna med bindestreck, t.ex. Skullsplitter-, Blodskalp-, Knivmanke-).

### Särskilda fall
- **Efterföljande spårtext efter beskrivningen** (källan har en engelsk avslutande rad direkt efter description, t.ex. 5943, 3366, 1270, 503, 99123, 92434, 1273, 5821, 7141, 79360, 3911): lagd i description-fältet enligt TASK A regel 3 (osäker gräns → tidigare fält); placering ej avgjord av människa.
- **3911**: gränsmellanslag mellan objectives/description ger en validatorvarning (`mellanslag i kanten`); partitionen kräver mellanslaget.
- **1270**: `$gbuddy:lady;` lämnad oöversatt (validatorn kräver oförändrad token).
- **79360**: titeln börjar med ett skadat tecken (U+FFFD) i källan; bevarat byte för byte.
- **95508 m.fl.**: Lord Admiral = Herr Amiral (beslut ovan).
- **Page text**: första tecknet i flera rader är ett parser-artefakttecken (`�`, `p`, `P`, `` ` ``, `@`, `0`, `-`); bevarat före den svenska texten så att merge-steget kan avgöra. 10544 ("Lok-tar ogar!") lämnad oöversatt (orkiska) → validatorvarning avsedd.
- **NPC**: `[DNT]`-rader, `Credit` (270574/270575) och interna trigger-/dummynamn är oöversatta eller minimalt översatta; titlar = referens, ej i utdata.

### Gameobjects — validatorn nekar på källan
`translation/batches/gameobjects-batch-01..07.tsv` innehåller **dubbletter av id** (cache 952 rader, 598 unika id). `validate-batch.py` svarar för varje batch
`FEL: kalla: id N forekommer flere ganger` (batch 01: 17 id; 02: 17; 03: 14; 04: 11; 05: 15; 06: 20; 07: 5) och sammanlagt `RESULTAT: N FEL ... rakna inte in batchen`.
Inga andra fel (kolumner, ordning, antal rader stämmer 1:1 med källan). Översättningarna ligger i `translation/out/gameobjects-batch-XX-sv.tsv` i exakt källordning,
men id→namn är tvetydigt för de upprepade id:na, så batcherna ska inte slås ihop innan id-kollisionen i `translation/gameobjectcache-en.tsv` / `tools/parse-wdb.py` lösts.
