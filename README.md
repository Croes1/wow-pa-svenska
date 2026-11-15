# Wow på Svenska

** NOTERA **
Detta är en fork på addonet "Världen av Krigskraft". Anledningen till forken är att addonet inte finns tillgängligt på GitHub och jag
ville bygga vidare på översättningarna då flera inte finns nu när WoW Forever ser annorlunda ut mot Classic.

Svensk översättning av **WoW Forever**. Addonet byter den engelska texten mot svensk
medan du spelar: uppdrag, föremål, förmågor, buffar, NPC-namn, chattmeddelanden och stora delar av
gränssnittet. Saknas en översättning står engelskan kvar, så inget går sönder.

> **Om översättningen:** nya översättningar är gjorda med AI (Gemmini och GLM-5.3-Flash) efter fasta regler och en gemensam ordlista.
> och granskas och rättas löpande, bland annat utifrån spelarnas rapporter. Hittar du något som låter
> fel, rapportera det (se nedan). Det är så den blir bra.
> Alla nya översättningar läggs in i filer kallade "extra-" för att göra det tydligt vilket som hanterats i forken (just nu). Resten
> av översättningarna kommer från addonet Världen av Krigskraft.

## Vad som är översatt

| Del | Läge |
|---|---|
| Föremål (namn och beskrivning) | alla, ca 17 700 |
| Förmågor | namn på nästan alla förmågor (ca 12 900, även fiendernas); beskrivningar för ca 3 200 |
| Buffar och debuffar | de vanligaste |
| Uppdrag | ca 1 700 av 4 200 med hela texten: alla uppdrag upp till nivå 30 för båda sidor, med klassuppdrag, instanser, slagfält och högtider. Fler läggs till löpande. |
| NPC-namn och dialog | ca 520 namn och 100 dialogtexter, plus varelserna i de översatta uppdragen |
| Gränssnittet | porträttmenyer, rollfigurspanelen, inställningarna, spelmenyn, kartan, spellboken, yrkesfönstret |
| Chatten | ca 190 sorters systemmeddelanden: byte, erfarenhet, anseende, grupp, uppdrag, auktioner … |
| Ortnamn | egna svenska namn: Skymningsskogen, Våtmarkerna, Mörkby, Stormvinds stad … |

## Installera

1. Ladda ner den senaste zip-filen under **Releases** på GitHub.
2. Packa upp den i `World of Warcraft/_forever_/Interface/AddOns/`, så att mappen
   `wow_pa_svenska` ligger direkt där (mappen och filen `wow_pa_svenska.toc` ska heta samma).
3. Starta spelet, eller skriv `/reload` om det redan är igång.

Klienten ska vara på **engelska** (enUS). Spelet finns inte på svenska; addonet översätter den engelska texten.

## Använda

- `/wps` öppnar inställningarna (även under *Alternativ → AddOns → Wow på Svenska*). Där kryssar du i
  vad som ska vara på svenska: uppdrag, dialog med NPC:er, föremål, besvärjelser och förmågor, NPC-namn,
  platsnamn, systemmeddelanden, fönster och högerklicksmenyer. Vill du till exempel ha uppdragen på svenska
  men besvärjelserna på engelska kryssar du ur *Besvärjelser och förmågor*. Det du kryssar ur visas på
  engelska överallt, också i besvärjelseboken och yrkesfönstret. Text som redan visas byts när fönstret
  öppnas igen; knappen *Ladda om gränssnittet* byter allt direkt.
- Samma sak från chatten: `/wps spell off`, `/wps quest on`, `/wps gossip off` (`/wps status` listar namnen).
- **Växla till engelska:** lägg en tangent under *Tangentbindningar → AddOns → Wow på Svenska*.
  Håll **Alt** över en tooltip för att se engelskan just där.
- `/wps fel <kommentar>` sparar det som senast visades (tooltip, castbar, dialog, chattrad, uppdrag) med
  både engelska och svenska, plus din kommentar. Exempel: `/wps fel borde heta "Flår" i castbaren`.
  Rapporterna hamnar i `WTF/Account/<konto>/SavedVariables/WPSDB.lua` först vid `/reload` eller
  utloggning – skicka den filen till oss (GitHub-issue/Discord), så rättar vi. Filen innehåller bara
  dina tilläggsinställningar och rapporterna (jag-fliken chattloggar eller andra spelare hamnar där ej).
- `/wps diag` visar vilka delar som är aktiva.

## Hjälp till: samla ny text

Uppdrag och NPC-dialog finns inte i någon databas som vi kan hämta ner — den engelska texten samlas
in i spelet. Det kräver dock **inget tillägg**: klienten skriver själv ner det den ser i cachefiler
under `Cache/WDB` medan du spelar.

Så här bidrar du (ett par minuters jobb):

1. Spela som vanligt med klienten på **engelska (enUS)** — öppna uppdrag och prata med NPC:er.
   Klienten sparar automatiskt uppdragstext i `Cache/WDB/questcache.wdb` och NPC-namn/titlar i
   `Cache/WDB/creaturecache.wdb`.
2. Stäng ner spelet och kopiera de två filerna till mappen `wow_pa_svenska`.
3. Kör parsern (ett program, helt offline):
   ```bash
   python3 tools/parse-wdb.py questcache.wdb tsv translation/questcache-en.tsv
   python3 tools/parse-wdb.py creaturecache.wdb tsv translation/creaturecache-en.tsv
   ```
4. Säg i VS Code-chatten: *"Ny data är sparad i translation/ — läs AGENTS.md och translation/PIPELINE.md
   och kör nästa översättningsrunda."* AI-agenten gör resten (segmentering, kontroller, översättning,
   sammanfogning — utan ett enda API-anrop).

Fel på en **befintlig** översättning? Använd istället `/wps fel <vad som är fel>` (se ovan): rapporten
sparas i `WTF/Account/<konto>/SavedVariables/WPSDB.lua` vid `/reload` eller utloggning — skicka filen.

(Ett frivilligt Collector-tillägg som samlar mer text — dialoger, zoner m.m. — är planerat men finns
inte ännu; WDB-cachefilerna ovan räcker för uppdrag och NPC-namn.)

## Kända begränsningar

- Namnen som spelet ritar över NPC:ers huvuden (utan namnplattor) kan inget addon ändra. Slå på
  namnplattor för vänliga NPC:er, så blir de svenska.
- Auktionshuset söker på engelska namn.
- Svenska texter är ibland längre än engelska och kan klippas i smala knappar.
- Blockeras *Sätt fokus* i porträttmenyn ("Interface action failed because of an AddOn"): stäng av
  *Högerklicksmenyer på porträtt* i `/wps` och rapportera det.

## För utvecklare

Översättningsrundor görs i den här mappen av **AI-agenten i VS Code-chatten** —
aldrig via något översättnings-API: inga externa AI-tjänster, modell-API:er
eller andra HTTP-endpoints är tillåtna (de borttagna API-verktygen ska inte
återskapas). Agentens startpunkt är
`AGENTS.md`, vidare till `translation/PIPELINE.md` (hur ny data sparas i
`translation/`, offline-verktygen i `tools/`, kontrollerna och STOPP före
merge). Svenska skrivregler står i `translation/PROMPT-translation.md`, och
termbasen finns i `translation/glossary-core.tsv`.

### Sammanfogning (merge) — så här

När en översättningsrunda är grön (alla `verify-segmentation.py`/`validate-batch.py`
rapporterar `RESULTAT: OK`, och fältplaceringarna för fragmenterna är beslutade i
`translation/batches/review/DECISIONS-*.md`) sammanfogas svenskorna så här:

1. **Torrkörning** (visar hur många rader som blir nya, skriver inget):
   ```bash
   python3 tools/merge-translation.py --torr
   ```
2. **Kör sammanfogningen:**
   ```bash
   python3 tools/merge-translation.py
   ```
   Verktyget skapar/applicerar två tilläggsfiler — `Data/QuestExtra.lua`
   (uppdrag: `[id]={t=…,o=…,d=…,p=…,c=…}`) och `Data/NpcExtra.lua`
   (`[id]="Namn"`) — och länkar in dem i `wow_pa_svenska.toc` efter
   `Data\Quest.lua` respektive `Data\Npc.lua`. **`Data/Quest.lua` och
   `Data/Npc.lua` röras aldrig**: id som redan finns där hoppas över, och
   laddningslooparna i extrafilerna har en nil-vakt (`if LQ[id] == nil`)
   som dubbelgaranti. Körningen kan upprepas hur många gånger som helst —
   filerna regenereras deterministiskt ur `translation/out/*.tsv`.
3. **Verifiera i lua5.1** (parser + att datan laddas som riktiga WPS-tabeller):
   ```bash
   lua5.1 -e "assert(loadfile('Data/QuestExtra.lua')); assert(loadfile('Data/NpcExtra.lua')); print('SYNTAX OK')"
   ```
   Runtime-check (räknar posterna; Data-filerna får WPS-stuben via varargs så
   att chunkarna laddas riktigt). OBS: heredoc-avslutet (`EOF`) måste stå i
   kolumn 1, så kopiera kodblocket nedan exakt så här det ser ut:

```
cat > /tmp/wps_check.lua <<'EOF'
local wps = { L = {} }
assert(loadfile("Data/Quest.lua"))(nil, wps)
assert(loadfile("Data/Npc.lua"))(nil, wps)
assert(loadfile("Data/QuestExtra.lua"))(nil, wps)
assert(loadfile("Data/NpcExtra.lua"))(nil, wps)
local q, n = 0, 0
for _ in pairs(wps.L.quest) do q = q + 1 end
for _ in pairs(wps.L.npc)  do n = n + 1 end
print("quest:", q, "npc:", n)
EOF
lua5.1 /tmp/wps_check.lua
python3 -m unittest discover -s tests   # ska sluta med OK
```
4. **Testa i spelet:** uppdatera kopian i `Interface/AddOns/`, `/reload` och
   besök något av de nya uppdragen/NPC:erna. Påminnelser:
   - Spårarrader (`l`-fältet i Data-filerna) följer inte med i dessa omgångar —
     objektraden i questspåraren förblir engelska tillsvidare.
   - Fragmenstrader (tom titel) hamnar i det fält som segmenteringen i
     `translation/segmented/` valde åt dem; besluten dokumenteras i
     `review/DECISIONS-*.md`.
   - Ångra en sammanfogning: ta bort `Data/QuestExtra.lua`, `Data/NpcExtra.lua`
     och de två raderna i `.toc`.

Bygg-pipelinen för releasepaketet (`pipeline/vak.py`: extract → validate →
merge → build, `python pipeline/release.py`) hör till det externa
projektrepot; inskickade collector-filer läggs där i
`pipeline/data/contrib/` (hålls utanför git) och tas med av `extract` och
`feedback`.

Handlagda tillägg till gränssnittet (flikar på karaktärssidan, färdigheter, anseende
och motsvarande) ligger i `Data/UiExtra.lua`, som laddas via `.toc` efter den
genererade `Data/Ui.lua`. Nybyggda strängar ska i första hand läggas i den filen,
så att `build` inte skriver över dem.

## Källor

- Speldatabaserna (föremål, besvärjelser, gränssnittstext) hämtas från [wago.tools](https://wago.tools).
- Den engelska uppdragstexten för uppdrag som collectorn inte har sett kommer från
  [cmangos classic-db](https://github.com/cmangos/classic-db) (GPL-3.0). Databasen laddas ner lokalt och
  ingår inte i addonet. Addonet innehåller de svenska översättningarna och de engelska titlar och
  målrader som behövs för att känna igen texten i questloggen.

## Licens och upphovsrätt

Koden i det här repot (addonets Lua-logik, verktygen under `tools/` och
översättningspipelinen) och de svenska översättningar som har gjorts i det här
projektet licensieras under **GPL-3.0-or-later** — GNU General Public License v3.0
eller senare version (se filen `LICENSE`). Bidrag som skickas in till projektet
antas läggas in på samma villkor.

- Forken bygger på addonet "Världen av Krigskraft" — tack till den ursprungliga
  skaparen (se notisen i början av filen).
- World of Warcraft® och Blizzard Entertainment® är varumärken eller registrerade
  varumärken som tillhör Blizzard Entertainment, Inc., i USA och/eller andra länder.
- Det här är ett fanprojekt och har ingen koppling till och är inte godkänt av
  Blizzard Entertainment.
- All speldatabastext (uppdrag, föremål, förmågor, NPC-namn m.m.) är © Blizzard
  Entertainment och omfattas **inte** av GPL-licensen ovan. De engelska
  originaltexterna ingår enbart för att addonet ska kunna känna igen och byta ut
  texten i spelet.
- Speldata från wago.tools och cmangos classic-db anges under *Källor* ovan.

