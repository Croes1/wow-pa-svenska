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
ui["This tribe of exiled trolls has joined forces with Thrall and the Horde.  They now call Durotar their home, which they share with their orc allies."] = "Den här stammen av förvisade troll har slagit sig samman med Thrall och Horden. De kallar numera Durotar för sitt hem, som de delar med sina orchallierade."

---------------------------------------------------------------------------
-- Färdigheter: yrkesbeskrivningar i höger panel
---------------------------------------------------------------------------
ui["Higher engineering skill allows you to learn higher level engineering schematics.  Schematics can be found on trainers around the world as well as from quests and monsters."] = "Högre ingenjörskonst gör att du kan lära dig planritningar på högre nivåer. Planritningar hittar du hos lärare runt om i världen samt från uppdrag och monster."

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
ui["Honor is gained by killing members of the opposite faction in PvP combat. You can use honor points to purchase special items."] = "Ära tjänas genom att döda medlemmar av motståndarsidan i PvP-strid. Du kan använda äropoäng för att köpa specialföremål."
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

---------------------------------------------------------------------------
-- [2026-11-15, omgång 2] Fullsvit ur /wps dump (217 strängar): statistik,
-- färdighets- och fraktionsbeskrivningar, statspanel, PvP/valuta. Material:
-- translation/ui/dump-2026-11-15-{en,sv}.tsv. Besluter i DECISIONS-filen.

---------------------------------------------------------------------------
-- Formatnycklar (siffror/markup fångas oförändrade)
---------------------------------------------------------------------------
ui["Language: %s"] = "Språk: %s"
ui["Language: Gutterspeak"] = "Språk: Rännspråk"
ui["Language: Orcish"] = "Språk: Orkiska"
ui["Each week, the Rank Points cap is increased, up to a maximum of |cnHIGHLIGHT_FONT_COLOR:%s|r for |cnHIGHLIGHT_FONT_COLOR:Rank %s|r."] = "Varje vecka ökas taket för gradpoäng, upp till som mest |cffffd200%s|r för |cffffd200grad %s|r."
ui["Rank Points: |cnHIGHLIGHT_FONT_COLOR:%s|r"] = "Gradpoäng: |cffffd200%s|r"
ui["Chance to |cFFFFFFFFHit|r, and to avoid being |cFFFFFFFFDodged|r or |cFFFFFFFFParried|r: %s\n\nChance to |cFFFFFFFFCritically Hit|r: %s\n\n|cFFFFFFFFGlancing Blows|r occur 100% of the time and deal 89% less damage"] = "Chans att |cffffffffträffa|r, och att undvika att bli |cffffffffväjd|r eller |cffffffffparerad|r: %s\n\nChans att |cffffffffträffa kritiskt|r: %s\n\n|cffffffffHalvträffar|r inträffar 100 % av tiden och gör 89 % mindre skada"
ui["Chance to |cFFFFFFFFHit|r: %s\n\nChance to |cFFFFFFFFCritically Hit|r: %s"] = "Chans att |cffffffffträffa|r: %s\n\nChans att |cffffffffträffa kritiskt|r: %s"
ui["|cffffd100Rank #%s for your level|r  |cffffffff%s|r"] = "|cffffd100Grad #%s för din nivå|r  |cffffffff%s|r"
ui["Not ranked at your level. Ranked from 1 to 30."] = "Ej rankad på din nivå. Rankas från 1 till 30."
ui["|cFFFFFFFFAgainst Raid Bosses|r"] = "|cffffffffMot raidbossar|r"
ui["|cFFFFFFFFEqual-Level Enemy|r"] = "|cffffffffJämnivåfiende|r"

---------------------------------------------------------------------------
-- Statistikkategorier och övergripande
---------------------------------------------------------------------------
ui[" Season 1"] = " Säsong 1"
ui["Battlegrounds"] = "Slagfält"
ui["Dungeons & Raids"] = "Instanser & rais"
ui["Dungeons and Raids"] = "Instanser och rais"
ui["Boss Kills"] = "Bossdräp"
ui["Kills"] = "Dräp"
ui["Creatures"] = "Varelser"
ui["Gear"] = "Utrustning"
ui["Consumables"] = "Förbrukningsartiklar"
ui["Travel"] = "Resor"
ui["Honorable Kills"] = "Ärorika dråp"
ui["Killing Blows"] = "Dödande slag"
ui["Alterac Valley Honorable Kills"] = "Ärorika dråp i Alteracdalen"
ui["Alterac Valley Killing Blows"] = "Dödande slag i Alteracdalen"
ui["Alterac Valley battles"] = "Strider i Alteracdalen"
ui["Alterac Valley towers captured"] = "Erövrade torn i Alteracdalen"
ui["Alterac Valley towers defended"] = "Försvarade torn i Alteracdalen"
ui["Alterac Valley victories"] = "Segrar i Alteracdalen"
ui["Arathi Basin Honorable Kills"] = "Ärorika dråp i Arathibäckenet"
ui["Arathi Basin Killing Blows"] = "Dödande slag i Arathibäckenet"
ui["Arathi Basin bases assaulted"] = "Angripna baser i Arathibäckenet"
ui["Arathi Basin bases defended"] = "Försvarade baser i Arathibäckenet"
ui["Arathi Basin battles"] = "Strider i Arathibäckenet"
ui["Arathi Basin victories"] = "Segrar i Arathibäckenet"
ui["Archmage Arugal kills (Shadowfang Keep)"] = "Ärkimagen Arugals dräp (Shadowfang Keep)"
ui["Average quests completed per day"] = "Uppdrag fullbordade i genomsnitt per dag"
ui["Bandage used most"] = "Mest använda förband"
ui["Bandages used"] = "Använda förband"
ui["Battleground Honorable Kills"] = "Ärorika dråp på slagfält"
ui["Battleground Killing Blows"] = "Dödande slag på slagfält"
ui["Battleground with the most Honorable Kills"] = "Slagfält med flest ärorika dråp"
ui["Battleground with the most Killing Blows"] = "Slagfält med flest dödande slag"
ui["Battlegrounds played"] = "Spelade slagfält"
ui["Battlegrounds won"] = "Vunna slagfält"
ui["Bazzalan kills (Ragefire Chasm)"] = "Bazzalans dräp (Ragefire Chasm)"
ui["Beverages consumed"] = "Konsumerade drycker"
ui["Blacksmithing Plans learned"] = "Lärda smidesritningar"
ui["Cairne Bloodhoof leads his people, the Proud Tauren, from this mighty Horde capital."] = "Cairne Bloodhoof leder sitt folk, de stolta taurenerna, från denna mäktiga hordhuvudstad."
ui["Capital of the Steamwheedle Cartel and home to goblinhood's finest engineers, alchemists and merchants."] = "Huvudstad i Ångvisslekartellen och hem för goblingsläktets främsta ingenjörer, alkemister och handelsmän."
ui["Deaths"] = "Dödsfall"
ui["Deaths from Hogger"] = "Dödsfall orsakade av Hogger"
ui["Deaths from Vanndar Stormpike"] = "Dödsfall orsakade av Vanndar Stormpike"
ui["Deaths from drowning"] = "Dödsfall genom drunkning"
ui["Deaths from falling"] = "Dödsfall genom fall"
ui["Deaths from fatigue"] = "Dödsfall av utmattning"
ui["Deaths from fire and lava"] = "Dödsfall genom eld och lava"
ui["Deaths in Alterac Valley"] = "Dödsfall i Alteracdalen"
ui["Deaths in Arathi Basin"] = "Dödsfall i Arathibäckenet"
ui["Deaths in Darkspear Islands"] = "Dödsfall på Darkspearöarna"
ui["Deaths in Warsong Gulch"] = "Dödsfall i Warsong Gulch"
ui["Different creature types killed"] = "Olika dräpta varelsestyper"
ui["Duels lost"] = "Förlorade dueller"
ui["Duels won"] = "Vunna dueller"
ui["Edwin VanCleef Kills (Deadmines)"] = "Edwin VanCleefs dräp (Deadmines)"
ui["Elixirs consumed"] = "Konsumerade elixir"
ui["Enchanting formulae learned"] = "Lärda förtrollningsformler"
ui["Engineering Schematics learned"] = "Lärda ingenjörsritningar"
ui["Epic items acquired"] = "Förvärvade episka föremål"
ui["Epic items looted"] = "Plundrade episka föremål"
ui["Equipped epic items in item slots"] = "Utrustade episka föremål i föremålsplatser"
ui["Expertise:"] = "Sakkunskap:"
ui["Extra bank slots purchased"] = "Köpta extra bankplatser"
ui["First Aid Manuals learned"] = "Lärda första-hjälpen-manualer"
ui["First Aid skill"] = "Färdighet i första hjälpen"
ui["Fish and other things caught"] = "Fångad fisk och annat"
ui["Fish caught"] = "Fångad fisk"
ui["Fishing daily quests completed"] = "Fullbordade fiskedaguppdrag"
ui["Fishing skill"] = "Fiskefärdighet"
ui["Flasks consumed"] = "Konsumerade elixirflaskor"
ui["Flight paths taken"] = "Använda flyglinjer"
ui["Food eaten"] = "Förtärd mat"
ui["Gold spent at barber shops"] = "Guld spenderat hos barberare"
ui["Gold spent on postage"] = "Guld spenderat på porto"
ui["Gold spent on talent tree respecs"] = "Guld spenderat på omspecialiseringar av talangträdet"
ui["Greed rolls made on loot"] = "Girighetsslag på byte"
ui["Health potions consumed"] = "Konsumerade läkande drycker"
ui["Higher cooking skill allows you to learn higher level cooking recipes.  Recipes can be found on trainers around the world as well as from quests and as drops from monsters."] = "Högre matlagningskunskap gör att du kan lära dig recept på högre nivåer. Recept hittar du hos lärare runt om i världen samt från uppdrag och som plundring från monster."
ui["Higher defense makes you harder to hit and makes monsters less likely to land a crushing blow."] = "Högre försvar gör dig svårare att träffa och gör att monster i mindre utsträckning landar ett förkrossande slag."
ui["Higher first aid skill allows you to learn higher level first aid abilities.  First aid abilities can be found on trainers around the world as well as from quests and as drops from monsters."] = "Högre första-hjälpen-kunskap gör att du kan lära dig första-hjälpen-förmågor på högre nivåer. Förmågorna hittar du hos lärare runt om i världen samt från uppdrag och som plundring från monster."
ui["Higher fishing skill increases your chance of catching fish in bodies of water around the world.  If you are having trouble catching fish in a given area, move to a lower level area or purchase a fishing lure and try again."] = "Högre fiskekunskap ökar din chans att fånga fisk i vattendrag runt om i världen. Har du svårt att fånga fisk i ett visst område, bege dig till ett område på lägre nivå eller köp ett fiskelock och försök igen."
ui["Higher mining skill allows you to harvest more difficult minerals nodes around the world.  If you cannot harvest a specific mineral, then increase your skill by mining easier to mine minerals in lower level areas."] = "Högre gruvbrytningskunskap låter dig bryta svårare mineraler runt om i världen. Kan du inte bryta en viss mineral, öka din kunskap genom att bryta lättare mineraler i områden på lägre nivå."
ui["Higher poison skill allows more powerful poisons to be crafted. Reagents can be purchased from poison vendors and shady dealers, then combined into deadly concoctions that rot, weaken, and wither foes."] = "Högre giftkunskap gör att starkare gifter kan framställas. Material köps av giftförsäljare och skumma handlare och kombineras till dödliga brygder som ruttnar, försvagar och förtär fiender."
ui["Higher skill increases your chance to hit."] = "Högre kunskap ökar din chans att träffa."
ui["Higher weapon skill increases your chance to hit."] = "Högre vapenkunskap ökar din chans att träffa."
ui["Highest Alchemy skill"] = "Högsta alkemikunskap"
ui["Highest Blacksmithing skill"] = "Högsta smideskunskap"
ui["Highest Enchanting skill"] = "Högsta förtrollningskunskap"
ui["Highest Engineering skill"] = "Högsta ingenjörskunskap"
ui["Highest Herbalism skill"] = "Högsta örtkunskap"
ui["Highest Inscription skill"] = "Högsta inskriptionskunskap"
ui["Highest Leatherworking skill"] = "Högsta lädersmideskunskap"
ui["Highest Mining skill"] = "Högsta gruvbrytningskunskap"
ui["Highest Skinning skill"] = "Högsta flåningskunskap"
ui["Highest Tailoring skill"] = "Högsta skrädderikunskap"
ui["Inscriptions learned"] = "Lärda inskriptioner"
ui["Items disenchanted"] = "Uttrullade föremål"
ui["Largest heal cast"] = "Största kastade läkning"
ui["Largest heal received"] = "Största mottagna läkning"
ui["Largest hit dealt"] = "Största utdelade träff"
ui["Largest hit received"] = "Största mottagna träff"
ui["Leatherworking Patterns learned"] = "Lärda lädersmidesmönster"
ui["Led by Sylvanas Windrunner, the Forsaken have joined a tenuous alliance with the Horde and established this capital in the vast depths under the Ruins of Lordaeron."] = "Under Sylvanas Windrunners ledning har de bortglömda ingått en skör allians med Horden och upprättat denna huvudstad i de djupa gångarna under Lordaerons ruiner."
ui["Legendary items acquired"] = "Förvärvade legendariska föremål"
ui["Mage Portals taken"] = "Använda magikerportaler"
ui["Mage portal taken most"] = "Mest använda magikerportal"
ui["Mana potions consumed"] = "Konsumerade manadrycker"
ui["Materials produced from disenchanting"] = "Material utvunna vid uttrullning"
ui["Mekgineer Thermaplugg kills (Gnomeregan)"] = "Mekgineer Thermapluggs dräp (Gnomeregan)"
ui["Most Horde factions at Exalted"] = "Flest hordfraktioner på Upphöjd"
ui["Most factions at Exalted"] = "Flest fraktioner på Upphöjd"
ui["Most factions at Honored or higher"] = "Flest fraktioner på Ärad eller högre"
ui["Most factions at Revered or higher"] = "Flest fraktioner på Vördad eller högre"
ui["Most gold ever owned"] = "Flest guld någonsin i ägo"
ui["Mounts owned"] = "Ägda ridjur"
ui["Mutanus the Devourer kills (Wailing Caverns)"] = "Mutanus den Uppslukares dräp (Wailing Caverns)"
ui["Nature:"] = "Natur:"
ui["Need rolls made on loot"] = "Behovsslag på byte"
ui["New Set"] = "Ny uppsättning"
ui["Number of hugs"] = "Antal kramar"
ui["Number of times hearthed"] = "Antal hemteleporteringar"
ui["Part of the Steamwheedle Cartel, this goblin city provides a neutral haven for those that wish to trade goods and services in the Barrens."] = "En del av Ångvisslekartellen; denna goblinstad erbjuder en neutral tillflykt för den som vill handla med varor och tjänster i Kargmarkerna."
ui["Powderfuse"] = "Krutstubinen"
ui["Professions at maximum skill"] = "Yrken på maxfärdighet"
ui["Professions learned"] = "Lärda yrken"
ui["Quests abandoned"] = "Övergivna uppdrag"
ui["Quests completed"] = "Fullbordade uppdrag"
ui["Rath'mael Kills (Ruins of Lordaeron)"] = "Rath'mael-dräp (Ruins of Lordaeron)"
ui["Rebirthed by druids"] = "Pånyttfödda av druiderna"
ui["Redeemed by paladins"] = "Förlossade av paladiner"
ui["Resurrected by priests"] = "Återupplivade av präster"
ui["Resurrected by soulstones"] = "Återupplivade av själstenar"
ui["Revived by druids"] = "Återväckta av druiderna"
ui["Secondary skills at maximum skill"] = "Sekundära färdigheter på maxfärdighet"
ui["Select a currency to view its details."] = "Välj en valuta för att se dess detaljer."
ui["Smelting Recipes learned"] = "Lärda smältningsrecept"
ui["Spirit returned to body by shamans"] = "Andar återförda till kroppen av schamaner"
ui["Summons accepted"] = "Antagna framkallningar"
ui["Tailoring Patterns learned"] = "Lärda skrädderimönster"
ui["The Earthen Ring is a loose collective of Horde-aligned shamans and druids who seek to maintain and nurture the balance of nature on Azeroth."] = "Jordringen är en lös sammanslutning av hordvänliga schamaner och drudier som söker bevara och vårda naturens balans på Azeroth."
ui["This booming coastal city is run by Baron Revilgaz of the Blackwater Raiders.  Mortal enemies of the Bloodsail Buccaneers and part of the Steamwheedle Cartel."] = "Den här blomstrande kuststaden drivs av baron Revilgaz från Blackwaters pirater. Dödsfiender till Blodssegelfribytarna och en del av Ångvisslekartellen."
ui["Total 10-player raids entered"] = "Totalt besökta 10-mans rais"
ui["Total 20-player raids entered"] = "Totalt besökta 20-mans rais"
ui["Total 40-player raids entered"] = "Totalt besökta 40-mans rais"
ui["Total 5-player dungeons entered"] = "Totalt besökta 5-mans instanser"
ui["Total Honorable Kills"] = "Totalt antal ärorika dråp"
ui["Total Killing Blows"] = "Totalt antal dödande slag"
ui["Total cheers"] = "Totalt antal hejarop"
ui["Total damage done"] = "Totalt utdelad skada"
ui["Total damage received"] = "Totalt mottagen skada"
ui["Total deaths"] = "Totalt dödsfall"
ui["Total deaths from opposite faction"] = "Totalt dödsfall orsakade av motståndarsidan"
ui["Total deaths from other players"] = "Totalt dödsfall orsakade av andra spelare"
ui["Total deaths in 10-player raids"] = "Totalt dödsfall i 10-mans rais"
ui["Total deaths in 20-player raids"] = "Totalt dödsfall i 20-mans rais"
ui["Total deaths in 40-player raids"] = "Totalt dödsfall i 40-mans rais"
ui["Total deaths in 5-player dungeons"] = "Totalt dödsfall i 5-mans instanser"
ui["Total facepalms"] = "Totala facepalms"
ui["Total factions encountered"] = "Totalt antal påträffade fraktioner"
ui["Total healing done"] = "Totalt utdelad läkning"
ui["Total healing received"] = "Totalt mottagen läkning"
ui["Total kills"] = "Totalt antal dräp"
ui["Total kills that grant experience or honor"] = "Totalt antal dräp som ger erfarenhet eller ära"
ui["Total raid and dungeon deaths"] = "Totalt dödsfall i instanser och rais"
ui["Total times LOL'd"] = "Totalt antal LOL"
ui["Total times playing world's smallest violin"] = "Antal gånger världens minsta fiol spelats"
ui["Total waves"] = "Totalt antal vågor"
ui["Vanity pets owned"] = "Ägda sällskapsdjur"
ui["Warsong Gulch Honorable Kills"] = "Ärorika dråp i Warsong Gulch"
ui["Warsong Gulch Killing Blows"] = "Dödande slag i Warsong Gulch"
ui["Warsong Gulch battles"] = "Strider i Warsong Gulch"
ui["Warsong Gulch flags captured"] = "Erövrade flaggor i Warsong Gulch"
ui["Warsong Gulch flags returned"] = "Återförda flaggor i Warsong Gulch"
ui["Warsong Gulch victories"] = "Segrar i Warsong Gulch"
ui["Weapon skills at maximum skill"] = "Vapenfärdigheter på maxfärdighet"
ui["World Honorable Kills"] = "Ärorika dråp i omvärlden"
ui["World Killing Blows"] = "Dödande slag i omvärlden"

---------------------------------------------------------------------------
-- Karaktärssidan: utrustningshanteraren (flikknapp)
---------------------------------------------------------------------------
ui["Equipment Manager"] = "Utrustningshanteraren"
ui["Equip"] = "Utrusta"
ui["Save"] = "Spara"
ui["A strong arm of the Steamwheedle Cartel, this port is home to seafaring sailors and back-alley dealers spanning the eastern sea trading routes."] = "Som en stark arm av Ångvisslekartellen är denna hamn hem för sjöfolk och bakgatshandlare som spänner över de östra sjöhandelsrutterna."
ui["Continent with the most Honorable Kills"] = "Världsdel med flest ärorika dråp"
ui["Continent with the most Killing Blows"] = "Världsdel med flest dödande slag"
ui["Cooking Recipes known"] = "Kända matlagningsrecept"
ui["Cooking daily quests completed"] = "Fullbordade matlagningsdaguppdrag"
ui["Cooking skill"] = "Matlagningsfärdighet"
ui["Creature type killed the most"] = "Oftast dräpt varelsestyp"
ui["Creatures killed"] = "Dräpta varelser"
ui["Critters killed"] = "Dräpta smådjur"
ui["Dalaran Cooking Awards gained"] = "Förvärvade matlagningsutmärkelser från Dalaran"
ui["Founded by Thrall, this Horde capital city is home to many of the proud orc clans of Durotar."] = "Denna hordhuvudstad grundades av Thrall och är hem för många av Durotars stolta orkklaner."
ui["Aku'mai kills (Blackfathom Deeps)"] = "Aku'mai-dräp (Blackfathom Deeps)"
ui["Alchemy Recipes learned"] = "Lärda alkemirecept"
ui["Allows the wearing of cloth armor."] = "Ger tillstånd att bära tygrustning."
ui["Allows the wearing of leather armor."] = "Ger tillstånd att bära läderrustning."
ui["Healthstones used"] = "Använda hälsostensar"
ui["Darkspear Islands Honorable Kills"] = "Ärorika dråp på Darkspearöarna"
ui["Darkspear Islands Killing Blows"] = "Dödande slag på Darkspearöarna"
ui["Darkspear Islands bases assaulted"] = "Angripna baser på Darkspearöarna"
ui["Darkspear Islands bases defended"] = "Försvarade baser på Darkspearöarna"
ui["Darkspear Islands battles"] = "Strider på Darkspearöarna"
ui["Darkspear Islands flags captured"] = "Erövrade flaggor på Darkspearöarna"
ui["Darkspear Islands victories"] = "Segrar på Darkspearöarna"