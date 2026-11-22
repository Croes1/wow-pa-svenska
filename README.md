# WoW på Svenska

*World of Warcraft, fast på svenska.*

A Swedish translation addon for **WoW Forever**. Explore Azeroth in your own language, from quests and items to abilities, NPCs and the game interface.

This project is a fork of **Världen av Krigskraft**, originally created by **Ninsew**. It builds on the original translations and adds new translations and support for WoW Forever.

New translations are AI-assisted and reviewed using shared terminology and translation guidelines. Player feedback helps improve them over time.

## Svenska

### Vad är översatt?

| Innehåll | Status |
|---|---|
| Föremål | Namn och beskrivningar, cirka 17 700 |
| Förmågor | Nästan alla namn och cirka 3 200 beskrivningar |
| Uppdrag | Cirka 2 100 av 4 200, inklusive alla uppdrag upp till nivå 30 för båda sidor |
| NPC:er | Cirka 4 400 namn och 100 dialogtexter |
| Buffar och debuffar | De vanligaste |
| Gränssnitt | Menyer, karaktärspanel, karta, spellista och yrkesfönster |
| Chatt | Cirka 190 typer av systemmeddelanden |
| Ortnamn | Svenska namn på platser och zoner |

Översättningen utvecklas löpande. Saknas en översättning visas originaltexten på engelska.

### Installation

1. Ladda ner den senaste versionen under [Releases](https://github.com/Croes1/wow-pa-svenska/releases).
2. Packa upp `wow_pa_svenska` i `World of Warcraft/_forever_/Interface/AddOns/`.
3. Starta spelet eller skriv `/reload`.

**Viktigt:** Spelklienten måste använda engelska (enUS).

### Användning

Öppna inställningarna med `/wps` eller via Alternativ → AddOns → Wow på Svenska.

Du kan själv välja vilka delar av spelet som ska översättas.

Några användbara kommandon:

| Kommando | Funktion |
|---|---|
| `/wps` | Öppnar inställningarna |
| `/wps status` | Visar aktiva översättningskategorier |
| `/wps spell off` | Stänger av översättning av förmågor |
| `/wps quest on` | Aktiverar uppdragsöversättning |
| `/wps meters on` | Visar avstånd i meter i stället för yards (av som standard) |
| `/wps diag` | Visar diagnostikinformation |
| `/wps fel <kommentar>` | Rapporterar en felaktig översättning |
| `/wps tipdebug on` / `off` | Loggar tooltips för felsökning (t.ex. text som blinkar) |

Du kan också hålla **Alt** över en tooltip för att tillfälligt visa den engelska texten.

### Hjälp till!

Hittat en konstig översättning? Använd `/wps fel <kommentar>` i spelet.

Rapporterna sparas i:

`WTF/Account/<konto>/SavedVariables/wow_pa_svenska.lua`

Skicka rapporten via ett [GitHub Issue](https://github.com/Croes1/wow-pa-svenska/issues) så kan översättningen granskas och rättas.

Vill du hjälpa till att samla in ny text? Spela med en engelsk klient, öppna uppdrag och prata med NPC:er. Spelet sparar automatiskt text i `Cache/WDB`. Dessa filer kan användas för att utöka översättningen.

### Kända begränsningar

- NPC-namn som visas direkt ovanför huvudet utan namnplattor kan inte översättas av addons.
- Auktionshuset söker med engelska namn.
- Svenska texter kan ibland vara längre än de engelska och klippas av i mindre gränssnittselement.

## English

### What is it?

A Swedish translation addon for WoW Forever. It replaces English game text with Swedish while you play.

The addon covers quests, items, abilities, NPCs, system messages, locations and much of the user interface.

It is a fork of **Världen av Krigskraft**, originally created by **Ninsew**. New translations are added and reviewed over time.

### Installation

1. Download the latest release from [GitHub Releases](https://github.com/Croes1/wow-pa-svenska/releases).
2. Extract `wow_pa_svenska` into `World of Warcraft/_forever_/Interface/AddOns/`.
3. Start the game or type `/reload`.

**The game client must use English (enUS).**

### Contributing

Found a mistranslation or want to help improve the addon?

- [Read the contribution guidelines](CONTRIBUTING.md).
- [Report a bug or suggest an improvement](https://github.com/Croes1/wow-pa-svenska/issues).
- Translating? The files in `Data/` are the addon's translations and are edited directly. Use the existing entries as a reference for tone and terminology; terminology decisions are comments in `Data/Glossary.lua`.
- Running the tools in `tools/`? The translation round, the style rules and a reusable translation prompt are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Sources and credits

- Original addon: **Världen av Krigskraft**, by **Ninsew**.
- Game data: [wago.tools](https://wago.tools).
- Quest source data: [cmangos classic-db](https://github.com/cmangos/classic-db).

## License and disclaimer

The code and original Swedish translations contributed to this project are licensed under [GPL-3.0-or-later](LICENSE).

World of Warcraft and all related game content are property of Blizzard Entertainment. This is an unofficial fan project and is not affiliated with or endorsed by Blizzard Entertainment.