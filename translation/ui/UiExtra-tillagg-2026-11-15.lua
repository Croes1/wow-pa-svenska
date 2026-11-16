-- UTKAST 2026-11-15 (granska före införande): nya gränssnittssträngar från
-- karaktärssidans fönster — statistik, valuta, PvP, yrkesbeskrivningar,
-- fraktionsbeskrivningar och statspanelen. Källor: skärmbilder, transkriberat
-- i translation/ui/screens-2026-11-15-{en,sv}.tsv, plan i UI-PLAN-2026-11-15.md.
-- OBS till platshållarna: poster med %s är formatsträngar; de kompileras av
-- WPS.CompileFormat (Chat.lua) precis som Data/Ui.lua:s "Level %d" — se not
-- i planen om att uppdatera huvudkommentaren i Data/UiExtra.lua.
local _, WPS = ...
local ui = WPS.L.ui

---------------------------------------------------------------------------
-- Statspanelen (rollfigur)
---------------------------------------------------------------------------
ui["Energy"] = "Energi"

---------------------------------------------------------------------------
-- Anseende: fraktionsbeskrivningen i höger panel
---------------------------------------------------------------------------
ui["This tribe of exiled trolls has joined forces with Thrall and the Horde. They now call Durotar their home, which they share with their orc allies."] = "Den här stammen av förvisade troll har slagit sig samman med Thrall och Horden. De kallar numera Durotar för sitt hem, som de delar med sina orchallierade."

---------------------------------------------------------------------------
-- Färdigheter: yrkesbeskrivning i höger panel
---------------------------------------------------------------------------
ui["Higher engineering skill allows you to learn higher level engineering schematics. Schematics can be found on trainers around the world as well as from quests and monsters."] = "Högre ingenjörskonst gör att du kan lära dig planritningar på högre nivåer. Planritningar hittar du hos lärare runt om i världen samt från uppdrag och monster."

---------------------------------------------------------------------------
-- Spelare mot spelare
---------------------------------------------------------------------------
ui["Season 1"] = "Säsong 1"
ui["Season %s"] = "Säsong %s" -- defensiv: om klienten säger "Season 2" o.d.
ui["Civilian"] = "Civilist"
ui["Rank Points: %s / %s"] = "Gradpoäng: %s / %s"
ui["Cap increase this week: %s"] = "Taket ökas den här veckan med: %s"
ui["Next Rewards at Rank %s"] = "Nästa belöningar vid grad %s"
ui["Faction Tabard"] = "Fraktionsvapenskjorta"
ui["Rewards may be purchased at the Hall of Legends in Orgrimmar."] = "Belöningar kan köpas i Legendarernas hall i Orgrimmar."
ui["Each week, the Rank Points cap is increased, up to a maximum of %s for Rank %s."] = "Varje vecka ökas taket för gradpoäng, upp till som mest %s för grad %s."

---------------------------------------------------------------------------
-- Valuta
---------------------------------------------------------------------------
ui["Honor Points"] = "Äropoäng"
ui["Honor is gained by killing members of the opposite faction in PVP combat. You can use honor points to purchase special items."] = "Ära tjänas genom att döda medlemmar av motståndarsidan i PvP-strid. Du kan använda äropoäng för att köpa specialföremål."
ui["Maximum"] = "Maximalt" -- alternativ: "Högsta antal"
ui["Unused"] = "Oanvända"
ui["Show on Backpack"] = "Visa på ryggväskan"

---------------------------------------------------------------------------
-- Statistik (titel, kategori och rader)
---------------------------------------------------------------------------
ui["Statistics"] = "Statistik"
ui["Wealth"] = "Förmögenhet"
ui["Times camped"] = "Gånger blivit campad" -- dataterm; granskas
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
