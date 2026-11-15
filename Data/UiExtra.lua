-- Tillägg till WPS.L.ui, tillagda för hand. Den här filen genereras inte av
-- pipeline/vak.py build (som bara skriver Data/Ui.lua) och skrivs alltså inte över
-- vid en ny build. Lägg därför nya gränssnittssträngar här, inte i Data/Ui.lua.
-- Alla poster är exakta matchningar (inga %s-format) och styrs av rutan
-- "Fönster och knappar" i /wps. Saknas en sträng i klienten sker inget – extra
-- poster som aldrig matchas är ofarliga.
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