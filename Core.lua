-- Wow på Svenska – kärna: inställningar, hjälpfunktioner och gemensamma uppslag.
-- Principer: bara hooksecurefunc/HookScript, aldrig ersätta Blizzards funktioner.
-- Saknas en översättning lämnas den engelska texten orörd.

local ADDON, WPS = ...

WPS.L = { quest = {}, item = {}, spell = {}, gossip = {}, npc = {}, zone = {}, ui = {}, names = {}, qtext = {} }
WPS.hooks = {}          -- namn -> true/false, visas av /wps diag
WPS.showOriginal = false -- växlas med tangenten, gäller bara denna session
WPS.last = {}           -- det som senast visades per ställe, för /wps fel

-- Sparar vad som senast visades på ett ställe (tooltip, castbar, gossip, chat, quest).
-- data innehåller id:n och både engelsk (en) och svensk (sv) text, så att en rapport
-- från /wps fel går att spåra tillbaka till rätt översättning.
function WPS.Remember(slot, data)
	data.at = time()
	WPS.last[slot] = data
end

local DEFAULTS = { quest = true, gossip = true, item = true, spell = true, npc = true, zone = true, chat = true, ui = true, uimenu = true, meters = false }

-- Rutorna i inställningspanelen (Options.lua) och /wps <namn> on|off. group styr rubriken i panelen.
WPS.CATEGORIES = {
	{ key = "quest", group = "Innehåll", label = "Uppdrag", desc = "Uppdragsfönster, uppdragslogg, kartans uppdragslista och spåraren" },
	{ key = "gossip", group = "Innehåll", label = "Dialog med NPC:er", desc = "Det NPC:er säger när du talar med dem, och dina svarsalternativ" },
	{ key = "item", group = "Innehåll", label = "Föremål", desc = "Namn och beskrivning i tooltips, namn i väskor, yrkes- och handelsfönster" },
	{ key = "spell", group = "Innehåll", label = "Besvärjelser och förmågor", desc = "Tooltips, buffar, castbars och namn i besvärjelseboken" },
	{ key = "npc", group = "Innehåll", label = "NPC-namn", desc = "Namn i tooltips och på ramar, NPC-repliker i chatten" },
	{ key = "zone", group = "Innehåll", label = "Platsnamn", desc = "Zoner vid områdesbyte, på minikartan och kartan" },
	{ key = "chat", group = "Gränssnitt", label = "Systemmeddelanden i chatten", desc = "Byte, anseende, erfarenhet och liknande" },
	{ key = "ui", group = "Gränssnitt", label = "Fönster och knappar", desc = "Rollfigurspanel, inställningar, spelmeny, karta och andra Blizzard-fönster" },
	{ key = "uimenu", group = "Gränssnitt", label = "Högerklicksmenyer", desc = "Menyerna på porträtt och i grupp- och vänlistan" },
	-- Inte en översättningskategori utan ett val; "Allt på/av" i panelen rör den inte (noall).
	{ key = "meters", group = "Gränssnitt", label = "Avstånd i meter", desc = "Räckvidd i tooltips räknas om från yards till meter (30 yd blir 27 m)", noall = true },
}

function WPS.Print(...)
	print("|cff33ff99WPS|r:", ...)
end

-- djb2. Samma hash ger nycklarna i Data/Gossip.lua (se Key i GossipText.lua).
function WPS.Hash(s)
	local h = 5381
	for i = 1, #s do
		h = (h * 33 + s:byte(i)) % 4294967296
	end
	return h
end

function WPS.On(category)
	return WPS.db and WPS.db[category] and not WPS.showOriginal
end

-- Namn utan id (spellboken, yrkesfönstret, kartan, chatten): engelska -> svenska, men bara ur de
-- kategorier som är påslagna. Ordlistans orter, varelser och föremål följer sina kategorier; resten av
-- ordlistan (fraktioner, raser, klasser) har ingen egen ruta och översätts alltid.
local NAME_TABLES = {
	{ "names_glossary_zone", "zone" }, { "names_glossary_npc", "npc" }, { "names_glossary_item", "item" },
	{ "names_general" }, { "names_npc", "npc" }, { "names_zone", "zone" },
	{ "names_spell", "spell" }, { "names_item", "item" },
}

function WPS.Name(text)
	if type(text) ~= "string" then return nil end
	for _, t in ipairs(NAME_TABLES) do
		local tbl = WPS.L[t[1]]
		local sv = tbl and tbl[text]
		if sv then
			if t[2] and WPS.On(t[2]) or not t[2] and not WPS.showOriginal then return sv end
			return nil -- namnet hör till en avstängd kategori: lämna engelskan
		end
	end
end

local function OnEvent(_, event, name)
	if event == "ADDON_LOADED" and name == ADDON then
		WPSDB = WPSDB or {}
		-- Dialog följde förr rutan för uppdrag: behåll spelarens val när den nya rutan dyker upp.
		if WPSDB.gossip == nil and WPSDB.quest ~= nil then WPSDB.gossip = WPSDB.quest end
		WPSDB.tipDebug = nil -- felsökningen slås på för hand varje session; loggen (tipLog) ligger kvar
		WPSDB.origLine = nil -- rutan finns inte längre (raden gav taint och togs bort)
		for k, v in pairs(DEFAULTS) do
			if WPSDB[k] == nil then WPSDB[k] = v end
		end
		WPS.db = WPSDB
	elseif event == "PLAYER_LOGIN" then
		for _, fn in ipairs(WPS.initFuncs or {}) do
			local ok, err = pcall(fn)
			if not ok then WPS.Print("Fel vid start:", err) end
		end
	end
end

-- Moduler registrerar sin start här, så att Blizzards fönster garanterat finns.
function WPS.OnLogin(fn)
	WPS.initFuncs = WPS.initFuncs or {}
	table.insert(WPS.initFuncs, fn)
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_LOGIN")
frame:SetScript("OnEvent", OnEvent)

---------------------------------------------------------------------------
-- Platshållare i texterna ($N, $C, $R, $B, $Gman:kvinna;)
---------------------------------------------------------------------------

local CLASS_SV = {
	WARRIOR = "Krigare", MAGE = "Magiker", PRIEST = "Präst", DRUID = "Druid", HUNTER = "Jägare",
	ROGUE = "Skurk", PALADIN = "Paladin", SHAMAN = "Schaman", WARLOCK = "Häxmästare",
}
local RACE_SV = {
	Human = "Människa", Dwarf = "Dvärg", NightElf = "Nattalv", Gnome = "Gnom", Orc = "Orch",
	Scourge = "Odöd", Tauren = "Tauren", Troll = "Troll",
}

function WPS.Expand(s)
	if type(s) ~= "string" or not s:find("$", 1, true) then return s end
	local name = UnitName("player") or ""
	local _, classFile, classLocal
	classLocal, classFile = UnitClass("player")
	local _, raceFile, raceLocal
	raceLocal, raceFile = UnitRace("player")
	local class = CLASS_SV[classFile] or classLocal or ""
	local race = RACE_SV[raceFile] or raceLocal or ""
	local female = UnitSex("player") == 3

	s = s:gsub("%$[Nn]", function() return name end)
	s = s:gsub("%$C", function() return class end)
	s = s:gsub("%$c", function() return class:lower() end)
	s = s:gsub("%$R", function() return race end)
	s = s:gsub("%$r", function() return race:lower() end)
	s = s:gsub("%$[Bb]", "\n")
	s = s:gsub("%$[Gg]([^:;]*):([^;]*);", function(m, f) return female and f or m end)
	return s
end

---------------------------------------------------------------------------
-- Växla original/svenska (tangent)
---------------------------------------------------------------------------

function WPS.Toggle()
	WPS.showOriginal = not WPS.showOriginal
	WPS.Print(WPS.showOriginal and "visar |cffffff00engelsk originaltext|r. Öppna om fönster och håll muspekaren över saker igen."
		or "visar |cff00ff00svenska|r igen.")
end

function WPS_ToggleOriginal()
	WPS.Toggle()
end

BINDING_HEADER_WPS = "Wow på Svenska"
BINDING_NAME_WPS_TOGGLE = "Växla mellan svenska och engelska"
