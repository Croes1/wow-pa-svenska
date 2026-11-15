-- Tillägg till WPS.L.ui, tillagda för hand. Den här filen genereras inte av
-- pipeline/vak.py build (som bara skriver Data/Ui.lua) och skrivs alltså inte över
-- vid en ny build. Lägg därför nya gränssnittssträngar här, inte i Data/Ui.lua.
-- Poster utan %s/%d matchas exakt; poster med %s/%d är formatsträngar och
-- kompileras av WPS.CompileFormat (Chat.lua), precis som Data/Ui.lua:s
-- "Level %d". Allt styrs av rutan "Fönster och knappar" i /wps. Saknas en
-- sträng i klienten sker inget – extra poster som aldrig matchas är ofarliga.
local _, WPS = ...
local ui = WPS.L.ui

---------------------------------------------------------------------------
-- Flikar och rubriker på karaktärssidan
---------------------------------------------------------------------------
ui["Character"] = "Rollfigur"
ui["Reputation"] = "Anseende"
ui["Skills"] = "Färdigheter"
ui["Pet"] = "Husdjur"
ui["Currency"] = "Valuta"
ui["Skill"] = "Färdighet"
ui["Titles"] = "Titlar"
ui["Title"] = "Titel"
ui["Rank"] = "Grad"
ui["Experience"] = "Erfarenhet"
ui["Mounts"] = "Ridjur"

---------------------------------------------------------------------------
-- Anseendegrader (FACTION_STANDING_LABEL_*).
-- Neutral, Friendly och Honored finns redan i Data/Ui.lua.
---------------------------------------------------------------------------
ui["Hated"] = "Hatad"
ui["Hostile"] = "Fientlig"
ui["Unfriendly"] = "Ovänlig"
ui["Revered"] = "Vördad"
ui["Exalted"] = "Upphöjd"

---------------------------------------------------------------------------
-- Klasser och raser som fristående ord (statspanel, tränare, anseende).
-- Samma ord som Core.lua (CLASS_SV/RACE_SV) använder i questtexter.
---------------------------------------------------------------------------
ui["Warrior"] = "Krigare"
ui["Mage"] = "Magiker"
ui["Priest"] = "Präst"
ui["Rogue"] = "Skurk" -- ersatte "Skälm" (ursprunglig översättning)
ui["Warlock"] = "Häxmästare"
ui["Hunter"] = "Jägare"
ui["Paladin"] = "Paladin"
ui["Shaman"] = "Schaman"
ui["Druid"] = "Druid"
ui["Human"] = "Människa"
ui["Dwarf"] = "Dvärg"
ui["Night Elf"] = "Nattalv"
ui["Gnome"] = "Gnom"
ui["Orc"] = "Orch"
ui["Tauren"] = "Tauren"
ui["Troll"] = "Troll"
ui["Blood Elf"] = "Blodalv"
ui["Draenei"] = "Draenei"

---------------------------------------------------------------------------
-- Statspanelen
---------------------------------------------------------------------------
ui["Armor"] = "Rustning"
ui["Defense"] = "Försvar"
ui["Melee"] = "Närstrid"
ui["Melee Attack Power"] = "Attackkraft i närstrid"
ui["Spell Power"] = "Besvärjelsekraft"
ui["All Resistances"] = "Alla motstånd"
ui["Fire Resistance"] = "Eldmotstånd"
ui["Fire Resist"] = "Eldmotstånd"
ui["Frost Resistance"] = "Frostmotstånd"
ui["Frost Resist"] = "Frostmotstånd"
ui["Nature Resistance"] = "Naturmotstånd"
ui["Nature Resist"] = "Naturmotstånd"
ui["Shadow Resistance"] = "Skuggmotstånd"
ui["Shadow Resist"] = "Skuggmotstånd"
ui["Arcane Resistance"] = "Arkanmotstånd"
ui["Arcane Resist"] = "Arkanmotstånd"
ui["Holy Resistance"] = "Heligt motstånd"
ui["Holy Resist"] = "Heligt motstånd"

---------------------------------------------------------------------------
-- Färdigheter: vapen, sekundära och yrken ("Skills"-fliken m.m.).
-- Daggers, Fist Weapons, Blacksmithing, Leatherworking, Skinning, First Aid,
-- Cooking och Fishing finns redan i Data/Ui.lua.
---------------------------------------------------------------------------
ui["Swords"] = "Svärd"
ui["Two-Handed Swords"] = "Tvåhandssvärd"
ui["Axes"] = "Yxor"
ui["Two-Handed Axes"] = "Tvåhandsyxor"
ui["Maces"] = "Klubbor"
ui["Two-Handed Maces"] = "Tvåhandsklubbor"
ui["Polearms"] = "Stångvapen"
ui["Staves"] = "Stavar"
ui["Bows"] = "Bågar"
ui["Guns"] = "Gevär"
ui["Crossbows"] = "Armborst"
ui["Thrown"] = "Kastvapen"
ui["Wands"] = "Trollstavar"
ui["Unarmed"] = "Obeväpnad"
ui["Riding"] = "Ridning"
ui["Lockpicking"] = "Dyrkning"
ui["Poisons"] = "Gifter"
ui["Herbalism"] = "Örtkunskap"
ui["Mining"] = "Gruvbrytning"
ui["Tailoring"] = "Skrädderi"
ui["Engineering"] = "Ingenjörskonst"
ui["Alchemy"] = "Alkemi"
ui["Enchanting"] = "Förtrollning"
ui["Jewelcrafting"] = "Juvelsmide"

-- Rubriker i grupperingen på färdighetsfliken
ui["Weapon Skills"] = "Vapenfärdigheter"
ui["Class Skills"] = "Klassfärdigheter"
ui["Secondary Skills"] = "Sekundära färdigheter"
ui["Armor Proficiencies"] = "Rustningsvanor"

-- Yrkes- och träningsgrader (Apprentice/Journeyman finns redan)
ui["Expert"] = "Expert"
ui["Artisan"] = "Hantverkare"
ui["Master"] = "Mästare"

---------------------------------------------------------------------------
-- Tränarfönstret
---------------------------------------------------------------------------
ui["Train"] = "Lär dig"
ui["Training"] = "Utbildning"
ui["Available"] = "Tillgängliga"

---------------------------------------------------------------------------
-- Husdjur
---------------------------------------------------------------------------
ui["Happy"] = "Glad"
ui["Content"] = "Nöjd"
ui["Unhappy"] = "Olycklig"

---------------------------------------------------------------------------
-- Fraktionsnamn som saknades i ordlistan (names_general i Data/Glossary.lua).
-- Övriga fraktioner finns redan där: Stormwind=Stormvind, Ironforge=Järnsmedjan,
-- Darnassus, Orgrimmar, Thunder Bluff=Dunderklippan, Undercity=Understaden,
-- Ratchet=Spärrhake, Everlook=Utkiken, Darkmoon Faire=Mörkmånemarknaden,
-- Steamwheedle Cartel=Ångvisslekartellen, Silverwing Sentinels m.fl.
---------------------------------------------------------------------------
ui["Gnomeregan Exiles"] = "Gnomeregans landsförvisade"
ui["Silvermoon City"] = "Silvermånstaden"
ui["Frostwolf Clan"] = "Frostvargsklanen"
ui["The Defilers"] = "Besudlarna"
ui["Timbermaw Hold"] = "Timmerkäftens hålla"
ui["Wintersaber Trainers"] = "Vintersabeltränarna"
ui["Hydraxian Waterlords"] = "Hydraxians vattenherrar"
ui["Zandalar Tribe"] = "Zandalarklanen"
ui["Brood of Nozdormu"] = "Nozdormus kull"
ui["Gelkis Clan Centaur"] = "Gelkisklanens kentaurer"
ui["Magram Clan Centaur"] = "Magramklanens kentaurer"

---------------------------------------------------------------------------
-- [2026-11-15] Karaktärssidan i sin helhet: statistik, valuta, PvP,
-- yrkesbeskrivningar, fraktionsbeskrivningar. Källsträngar med id:er i
-- translation/ui/screens-2026-11-15-{en,sv}.tsv; beslut, alternativ och
-- plan i translation/ui/UI-PLAN-2026-11-15.md + DECISIONS-2026-11-15.md.
---------------------------------------------------------------------------

---------------------------------------------------------------------------
-- Rollfigur: statspanelen
---------------------------------------------------------------------------
ui["Energy"] = "Energi"

---------------------------------------------------------------------------
-- Anseende: fraktionsbeskrivningar i höger panel
---------------------------------------------------------------------------
ui["This tribe of exiled trolls has joined forces with Thrall and the Horde. They now call Durotar their home, which they share with their orc allies."] = "Den här stammen av förvisade troll har slagit sig samman med Thrall och Horden. De kallar numera Durotar för sitt hem, som de delar med sina orchallierade."

---------------------------------------------------------------------------
-- Färdigheter: yrkesbeskrivningar i höger panel
---------------------------------------------------------------------------
ui["Higher engineering skill allows you to learn higher level engineering schematics. Schematics can be found on trainers around the world as well as from quests and monsters."] = "Högre ingenjörskonst gör att du kan lära dig planritningar på högre nivåer. Planritningar hittar du hos lärare runt om i världen samt från uppdrag och monster."

---------------------------------------------------------------------------
-- Spelare mot spelare (gradpoäng, veckotak, belöningar)
---------------------------------------------------------------------------
ui["Season 1"] = "Säsong 1"
ui["Season %s"] = "Säsong %s" -- skydd om klienten skriver "Season 2" o.d.
ui["Civilian"] = "Civilist"
ui["Rank Points: %s / %s"] = "Gradpoäng: %s / %s"
ui["Cap increase this week: %s"] = "Taket ökas den här veckan med: %s"
ui["Next Rewards at Rank %s"] = "Nästa belöningar vid grad %s"
ui["Faction Tabard"] = "Fraktionsvapenskjorta"
ui["Rewards may be purchased at the Hall of Legends in Orgrimmar."] = "Belöningar kan köpas i Legendarernas hall i Orgrimmar."
ui["Each week, the Rank Points cap is increased, up to a maximum of %s for Rank %s."] = "Varje vecka ökas taket för gradpoäng, upp till som mest %s för grad %s."

---------------------------------------------------------------------------
-- Valuta (äropoäng och gränssnittet runt listan)
---------------------------------------------------------------------------
ui["Honor Points"] = "Äropoäng"
ui["Honor is gained by killing members of the opposite faction in PVP combat. You can use honor points to purchase special items."] = "Ära tjänas genom att döda medlemmar av motståndarsidan i PvP-strid. Du kan använda äropoäng för att köpa specialföremål."
ui["Maximum"] = "Maximalt" -- alternativ: "Högsta antal"
ui["Unused"] = "Oanvända"
ui["Show on Backpack"] = "Visa på ryggväskan"

---------------------------------------------------------------------------
-- Statistik (titel, kategorier och rader)
---------------------------------------------------------------------------
ui["Statistics"] = "Statistik"
ui["Wealth"] = "Förmögenhet"
ui["Times camped"] = "Gånger blivit campad" -- dataterm; beslut i planen
ui["Talent tree respecs"] = "Omspecialiseringar av talangträdet" -- alternativ: "Ändringar av talangträdet"
ui["Total gold acquired"] = "Totalt samlat guld"
ui["Average gold earned per day"] = "Genomsnittligt förtjänat guld per dag"
ui["Gold looted"] = "Plundrat guld"
ui["Gold from quest rewards"] = "Guld från uppdragsbelöningar"
ui["Gold earned from auctions"] = "Guld intjänat på auktioner"
ui["Auctions posted"] = "Upplagda auktioner"
ui["Auction purchases"] = "Auktionsköp"
ui["Most expensive bid on auction"] = "Dyresta budet på auktion"
ui["Most expensive auction sold"] = "Dyresta sålda auktionen"
ui["Gold from vendors"] = "Guld från handlare"
ui["Gold spent on travel"] = "Guld spenderat på resor"