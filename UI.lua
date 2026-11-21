-- Gränssnittet: högerklicksmenyer på porträtt, rollfigurspanelen, inställningarna, spelmenyn,
-- kartan, spellboken och yrkesfönstret.
--
-- WPS.L.ui (Data/Ui.lua) är engelsk text -> svensk text. Texterna byts EFTER att Blizzard har satt
-- dem: SetText på en FontString är inte skyddat, så inget taint följer med till Blizzards kod.
-- De globala strängarna (SET_FOCUS ...) skrivs aldrig över; det skulle smitta skyddad kod som läser dem.
--
-- Menyer: Menu.ModifyMenu, Blizzards väg för addons att ändra menyer. Varje rad får en initializer
--   som byter texten på knappen när menyn ritas.
-- Fönster: medan ett fönster är öppet gås dess synliga texter igenom några gånger i sekunden. Listor
--   i ScrollBox återanvänder sina rader när man rullar eller byter kategori, så en enstaka genomgång
--   vid OnShow räcker inte.

local _, WPS = ...

local isSecret = issecretvalue or function() return false end

local exact = {}   -- engelska -> svenska
local formats = {} -- { pat, order, sv, literal } för texter med %s/%d

local function BuildMaps()
	local compile = WPS.CompileFormat
	for en, sv in pairs(WPS.L.ui or {}) do
		if en:find("%%[%d%$%.%-]*[sdfi]") and compile then
			local pat, order, literal = compile(en)
			formats[#formats + 1] = { pat = pat, order = order, sv = sv, literal = literal }
		else
			exact[en] = sv
		end
	end
	table.sort(formats, function(a, b) return a.literal > b.literal end)
end

-- Fyller i den svenska formatsträngen med fångsterna. %1$s pekar ut argument; annars i tur och ordning.
-- Fångsterna sätts in som text, så "46.4" (koordinat i ett %d-fält) blir inte avrundat eller fel.
local function Fill(fmt, args)
	local seq = 0
	return (fmt:gsub("%%(%d*)(%$?)[%-%.%d]*([sdfi%%])", function(num, dollar, conv)
		if conv == "%" then return "%" end
		seq = seq + 1
		return args[(dollar == "$" and tonumber(num)) or seq] or ""
	end))
end

-- Namn utan id: spells i spellboken, items i yrkes- och bytesfönstret, zoner på kartan, NPC:er.
-- Uppdragstexter (titel, mål, målrad "#/# X") ligger i qtext.
local function QText(text)
	return WPS.On("quest") and WPS.L.qtext[text] or nil
end

local function Name(text)
	return exact[text] or WPS.Name(text) or QText(text)
end

local Translate

local function TranslatePlain(text, depth)
	local sv = Name(text)
	if sv then return sv end
	-- "Movement Speed:" byggs av STAT_FORMAT ("%s:") och etiketten.
	local base = text:match("^(.-):$")
	if base and base ~= "" then
		sv = Name(base)
		if sv then return sv .. ":" end
	end
	-- Uppdragstitel med nivå och gruppstorlek framför: "[3] [29] Razormaw Needling", "[25+] WANTED: X".
	local prefix, title = "", text
	while true do
		local p, r = title:match("^(%[[^%]]*%]%s*)(.+)$")
		if not p then break end
		prefix, title = prefix .. p, r
	end
	if prefix ~= "" then
		sv = QText(title)
		if sv then return prefix .. sv end
	end
	-- Målrad och yrkesrad med räknare: "0/10 Razormaw Incisor", "Leatherworking 102/150".
	local count, rest = text:match("^(%d+/%d+) (.+)$")
	if count then
		local line = QText("#/# " .. rest)
		if line then return (line:gsub("#/#", count, 1)) end
		local who = rest:match("^(.+) slain$")
		local whoSv = who and WPS.On("quest") and WPS.Name(who)
		if whoSv then return count .. " " .. whoSv .. " dödade" end
		sv = Name(rest)
		if sv then return count .. " " .. sv end
	end
	local label, count2 = text:match("^(.-) (%d+/%d+)$")
	if label then
		sv = Name(label)
		if sv then return sv .. " " .. count2 end
	end
	-- NPC-titel under namnet: "<Innkeeper>".
	local npcTitle = text:match("^<(.+)>$")
	if npcTitle then
		sv = Name(npcTitle)
		if sv then return "<" .. sv .. ">" end
	end
	for _, f in ipairs(formats) do
		local caps = { text:match(f.pat) }
		if caps[1] ~= nil then
			local args = {}
			-- Argumenten översätts också: "Pass on Loot: No", "Level 27 |cff..Hunter|r", "%s (Complete)".
			for i, n in ipairs(f.order) do
				local a = caps[i]
				args[n] = (depth < 2 and Translate(a, depth + 1)) or a
			end
			return Fill(f.sv, args)
		end
	end
end

-- Färgkod runt hela texten ("|cffffd100Stats:|r") behålls.
function Translate(text, depth)
	depth = depth or 0
	if text == "" then return nil end
	local sv = TranslatePlain(text, depth)
	if sv then return sv end
	local pre, inner, post = text:match("^(|c%x%x%x%x%x%x%x%x)(.-)(|r)$")
	if inner then
		sv = TranslatePlain(inner, depth)
		if sv then return pre .. sv .. post end
	end
end
WPS.UITranslate = function(text) return Translate(text, 0) end

local function Apply(fs)
	local text = fs:GetText()
	if isSecret(text) or type(text) ~= "string" or text == "" then return end
	local sv = Translate(text)
	if sv and sv ~= text then
		fs:SetText(sv)
		WPS.Remember("ui", { en = text, sv = sv })
	end
end

-- Blizzard skriver om många texter vid varje uppdatering (rollfigurspanelen vid varje stats-, aura- och
-- regenhändelse). Genomgången hinner då visa engelskan en stund: det blinkar. Därför får varje
-- FontString som genomgången hittar en efterhand-hook på SetText, så att svenskan sätts direkt efter
-- Blizzards text, innan något ritas. Ticker-genomgången behövs fortfarande för nya rader i listor.
local hookedFS = setmetatable({}, { __mode = "k" })
local busy = false

local function AfterSetText(fs)
	if busy or not WPS.On("ui") then return end
	busy = true
	pcall(Apply, fs)
	busy = false
end

local function HookFontString(fs)
	if hookedFS[fs] then return end
	hookedFS[fs] = true
	pcall(hooksecurefunc, fs, "SetText", AfterSetText)
	pcall(hooksecurefunc, fs, "SetFormattedText", AfterSetText)
end

local function Walk(frame, depth)
	if (frame.IsForbidden and frame:IsForbidden()) or not frame:IsVisible() then return end
	for _, r in ipairs({ frame:GetRegions() }) do
		if r:GetObjectType() == "FontString" and r:IsVisible() then
			HookFontString(r)
			busy = true
			pcall(Apply, r)
			busy = false
		end
	end
	if depth < 30 then
		for _, child in ipairs({ frame:GetChildren() }) do
			Walk(child, depth + 1)
		end
	end
end

local function SafeWalk(frame)
	if WPS.On("ui") then pcall(Walk, frame, 0) end
end

---------------------------------------------------------------------------
-- Fönster
---------------------------------------------------------------------------

-- Gås igenom medan de är öppna.
local PANELS = {
	"CharacterFrame", "SettingsPanel", "GameMenuFrame", "PlayerSpellsFrame", "ProfessionsFrame",
	"WorldMapFrame", "MailFrame", "MerchantFrame", "LootFrame", "TaxiFrame", "FriendsFrame",
	"StaticPopup1", "StaticPopup2", "StaticPopup3", "ContainerFrame1", "ContainerFrameCombinedBags",
	"ClassTrainerFrame", "AuctionHouseFrame", "InspectFrame", "DressUpFrame", "PVEFrame", "LFGParentFrame",
	"CommunitiesFrame", "TradeFrame", "BankFrame", "GroupLootFrame1", "GroupLootFrame2", "GroupLootFrame3",
	"GroupLootFrame4", "LootHistoryFrame", "GossipFrame", "PetStableFrame", "TabardFrame", "AddonList",
	"MacroFrame", "ReadyCheckFrame", "BattlefieldFrame", "PVPFrame", "HonorFrame", "WorldStateScoreFrame",
}
-- Alltid synliga småbitar: gås igenom då och då.
local STATIC = {
	"ObjectiveTrackerFrame.Header", "QuestObjectiveTracker.Header", "CompactPartyFrameTitle",
	"CompactRaidFrameManager", "ChatFrame1Tab", "ChatFrame2Tab", "ChatFrame3Tab",
}
local INTERVAL = 0.2

local function Lookup(path)
	local t = _G
	for part in path:gmatch("[^.]+") do
		if type(t) ~= "table" then return nil end
		t = t[part]
	end
	return type(t) == "table" and t or nil
end

local hooked, tickers = {}, {}

local function HookPanels()
	for _, name in ipairs(PANELS) do
		local f = _G[name]
		if f and not hooked[name] and f.HookScript then
			local ok = pcall(function()
				f:HookScript("OnShow", function(self)
					SafeWalk(self)
					if tickers[name] then tickers[name]:Cancel() end
					tickers[name] = C_Timer.NewTicker(INTERVAL, function() SafeWalk(self) end)
				end)
				f:HookScript("OnHide", function()
					if tickers[name] then tickers[name]:Cancel() end
					tickers[name] = nil
				end)
			end)
			hooked[name] = ok
			if ok and f:IsVisible() then SafeWalk(f) end
		end
	end
	local n = 0
	for _, ok in pairs(hooked) do if ok then n = n + 1 end end
	WPS.hooks["UI-fönster"] = n > 0 and (n .. " st") or false
end

local function WalkStatic()
	for _, path in ipairs(STATIC) do
		local f = Lookup(path)
		if f and f.GetRegions then SafeWalk(f) end
	end
end

-- Tooltips utan datatyp (t.ex. fliktooltipsen på karaktärssidan): GameTooltip
-- läggs inte ut via TooltipDataProcessor och finns inte i PANELS, så den gås
-- igenom vid OnShow och sedan medan den syns (innehållet fylls ofta på efter
-- att tooltipen visats). Post-hooks bara, alltså ingen taint.
local function HookGameTooltip()
	local f = GameTooltip
	if not f or hooked.GameTooltip or not f.HookScript then return end
	local ok = pcall(function()
		f:HookScript("OnShow", function(self)
			SafeWalk(self)
			if tickers.GameTooltip then tickers.GameTooltip:Cancel() end
			tickers.GameTooltip = C_Timer.NewTicker(INTERVAL, function()
				if self:IsVisible() then
					SafeWalk(self)
				elseif tickers.GameTooltip then
					tickers.GameTooltip:Cancel()
					tickers.GameTooltip = nil
				end
			end)
		end)
		f:HookScript("OnHide", function()
			if tickers.GameTooltip then tickers.GameTooltip:Cancel() end
			tickers.GameTooltip = nil
		end)
	end)
	hooked.GameTooltip = ok
	WPS.hooks["Fliktooltips (GameTooltip)"] = ok
end

---------------------------------------------------------------------------
-- /wps dump: samlar osträngade texter från de fönster som är öppna
-- (statistik-, anseende- och färdighetslistorna måste skrollas/-klickas
-- igenom). Material för en uppdateringsrunda — som /wps fel, men allt på
-- en gång. Sparas i WPSDB.uiDump (SavedVariables) med fönstret som först
-- visade texten som värde; /reload eller utloggning sparar filen.
---------------------------------------------------------------------------
local function DumpFrame(frame, out, depth)
	if (frame.IsForbidden and frame:IsForbidden()) or not frame:IsVisible() then return end
	for _, r in ipairs({ frame:GetRegions() }) do
		if r:GetObjectType() == "FontString" and r:IsVisible() then
			local text = r:GetText()
			if type(text) == "string" and text ~= "" and not isSecret(text)
				and text:find("[A-Za-z]") and not text:find("|H")
				and Translate(text, 0) == nil then
				out[text] = out[text] or (frame.GetName and frame:GetName() or "?")
			end
		end
	end
	if depth < 30 then
		for _, child in ipairs({ frame:GetChildren() }) do
			DumpFrame(child, out, depth + 1)
		end
	end
end

local dumpTicker, dumpSession = nil, 0

local function DumpPass()
	local db = WPS.db
	if not db then return 0, 0 end
	db.uiDump = db.uiDump or {}
	local before = 0
	for _ in pairs(db.uiDump) do before = before + 1 end
	for _, name in ipairs(PANELS) do
		local f = _G[name]
		if f and f.IsVisible and f:IsVisible() then pcall(DumpFrame, f, db.uiDump, 0) end
	end
	if GameTooltip and GameTooltip.IsVisible and GameTooltip:IsVisible() then
		pcall(DumpFrame, GameTooltip, db.uiDump, 0)
	end
	local total = 0
	for _ in pairs(db.uiDump) do total = total + 1 end
	return total - before, total
end

local function DumpStop()
	if dumpTicker then dumpTicker:Cancel() dumpTicker = nil end
	dumpSession = dumpSession + 1
	local total = 0
	if WPS.db and WPS.db.uiDump then
		for _ in pairs(WPS.db.uiDump) do total = total + 1 end
	end
	WPS.Print(("dump: klar — %d texter total. /reload eller logga ut för att spara, skicka sedan wow_pa_svenska.lua (WTF/Account/<konto>/SavedVariables)."):format(total))
end

function WPS.UIDump(arg)
	if not WPS.db then return end
	if arg == "stop" or arg == "0" then DumpStop() return end
	if not WPS.On("ui") then
		WPS.Print("dump: rutan \"Fönster och knappar\" är av — kryssa i den först.")
		return
	end
	local seconds = tonumber(arg) or 60
	if dumpTicker then dumpTicker:Cancel() dumpTicker = nil end
	dumpSession = dumpSession + 1
	local session = dumpSession
	local added, total = DumpPass()
	WPS.Print(("dump: %d nya texter direkt (%d su). Samplar %d sekunder — klicka/skrolla igenom listorna; sluta tidigt med /wps dump stop."):format(added, total, seconds))
	dumpTicker = C_Timer.NewTicker(0.5, function()
		if session ~= dumpSession then return end
		local a, t = DumpPass()
		if t >= 5000 then
			DumpStop()
			WPS.Print("dump: uppnått maxantalet (5000) — stoppar.")
			return
		end
		if a > 0 then WPS.Print(("dump: %d nya (su %d)"):format(a, t)) end
	end, math.max(1, math.floor(seconds / 0.5)))
	C_Timer.After(seconds + 0.2, function()
		if session ~= dumpSession then return end
		DumpStop()
	end)
end

---------------------------------------------------------------------------
-- Menyer
---------------------------------------------------------------------------

local MENU_TAGS = {
	"SELF", "TARGET", "PARTY", "PLAYER", "PET", "OTHERPET", "FOCUS", "RAID", "RAID_PLAYER", "ENEMY_PLAYER",
	"FRIEND", "FRIEND_OFFLINE", "BN_FRIEND", "BN_FRIEND_OFFLINE", "CHAT_ROSTER", "GUILD", "GUILD_OFFLINE",
	"COMMUNITIES_GUILD_MEMBER", "COMMUNITIES_WOW_MEMBER", "BOSS", "ARENAENEMY", "VEHICLE", "RECENT_ALLY",
}

local function TranslateButton(button)
	if not WPS.On("uimenu") then return end
	pcall(function()
		for _, r in ipairs({ button:GetRegions() }) do
			if r:GetObjectType() == "FontString" then Apply(r) end
		end
	end)
end

-- Rader och undermenyer (Målmarkering -> Stjärna ...) får samma initializer.
local function Decorate(desc, depth)
	if desc.AddInitializer then desc:AddInitializer(TranslateButton) end
	if depth < 4 and desc.EnumerateElementDescriptions then
		for _, child in desc:EnumerateElementDescriptions() do Decorate(child, depth + 1) end
	end
end

local function HookMenus()
	if not (Menu and Menu.ModifyMenu) then
		WPS.hooks["Menu.ModifyMenu"] = false
		return
	end
	for _, tag in ipairs(MENU_TAGS) do
		pcall(Menu.ModifyMenu, "MENU_UNIT_" .. tag, function(_, root)
			if not WPS.On("uimenu") then return end
			pcall(function()
				for _, desc in root:EnumerateElementDescriptions() do Decorate(desc, 1) end
			end)
		end)
	end
	WPS.hooks["Menu.ModifyMenu"] = true
end

---------------------------------------------------------------------------

WPS.OnLogin(function()
	BuildMaps()
	HookMenus()
	HookPanels()
	HookGameTooltip()
	WalkStatic()
	C_Timer.NewTicker(3, WalkStatic)
	-- Blizzard_*-fönster som laddas vid behov (spellboken, yrkena) finns först efter sitt ADDON_LOADED.
	local f = CreateFrame("Frame")
	f:RegisterEvent("ADDON_LOADED")
	f:SetScript("OnEvent", function() HookPanels() end)
end)
