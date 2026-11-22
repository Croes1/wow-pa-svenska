-- Item-, spell-, buff- och NPC-tooltips via TooltipDataProcessor (efterhook, ingen ersättning av Blizzards kod).
-- Håll Alt för att se engelskan. Items får en grå rad med originalnamnet (AH-sökning kräver engelska).

local _, WPS = ...

local GREY = { 0.6, 0.6, 0.6 }
local isSecret = issecretvalue or function() return false end

local function Norm(s)
	s = (s or ""):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("\r\n", "\n")
	return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

-- Letar efter raden vars engelska text matchar. Returnerar rad, prefix, suffix så att
-- citattecken och "Use: " kan sättas tillbaka runt den svenska texten.
local function FindLine(tooltip, matches)
	local name = tooltip:GetName()
	if not name then return end
	for i = 2, tooltip:NumLines() do
		local fs = _G[name .. "TextLeft" .. i]
		local text = fs and fs:GetText()
		if text then
			local plain = Norm(text)
			local candidates = {
				{ plain, "", "" },
				{ plain:match('^"(.*)"$'), '"', '"' },
				{ plain:match("^Use: (.*)$"), "Använd: ", "" },
			}
			for _, c in ipairs(candidates) do
				if c[1] and matches(c[1]) then return fs, c[2], c[3] end
			end
		end
	end
end

local function Active(category)
	return WPS.On(category) and not IsAltKeyDown()
end

---------------------------------------------------------------------------
-- Tooltiplogg för felsökning: /wps tipdebug on|off (Options.lua).
-- Loggar vad som händer med GameTooltip: varje ombygge och vad addonen gjorde (post), raderna spelet
-- byggde tooltipen av (dlines/dline), varje rad som ändrar text (frame) och vad UI-genomgången
-- översatte (walk-set, UI.lua). Hamnar i WPSDB.tipLog (SavedVariables, skrivs vid /reload eller
-- utloggning), så att en spelare kan skicka filen. Av som standard och vid varje inloggning (Core.lua);
-- avstängd kostar den en tabelluppslagning per bildruta.
---------------------------------------------------------------------------

local TIPLOG_MAX = 1500

local function Show(v)
	if isSecret(v) then return "<secret>" end
	return tostring(v)
end

function WPS.TipLog(...)
	local db = WPS.db
	if not (db and db.tipDebug) then return end
	local log = db.tipLog
	if not log then log = {}; db.tipLog = log end
	local parts = {}
	for i = 1, select("#", ...) do parts[i] = Show((select(i, ...))) end
	log[#log + 1] = ("%.3f %s"):format(GetTime(), table.concat(parts, " "))
	if #log > TIPLOG_MAX then table.remove(log, 1) end
end

local function Line1(tooltip)
	local name = tooltip.GetName and tooltip:GetName()
	local fs = name and _G[name .. "TextLeft1"]
	return fs and fs:GetText()
end

---------------------------------------------------------------------------
-- Blizzards egna rader (typ "Leather", "Main Hand", "Instant")
--
-- Spelet bygger om en tooltip som visas ungefär fem gånger i sekunden, och då står allt på engelska
-- igen. Raderna översätts därför här, i samma bildruta som ombygget, i stället för av UI-genomgången
-- (UI.lua), som kommer några bildrutor senare och gör att texten blinkar.
--
-- Blizzards rader känns igen på texten i data.lines (det tooltipen byggdes av). Rader som andra addons
-- lägger till finns inte där och lämnas orörda, även om ordlistan råkar ha en översättning.
-- Raderna matchas på text och inte på radnummer: i spelltooltips saknar vissa data.lines text och
-- visas inte, så numren glider isär.
---------------------------------------------------------------------------

-- data.lines har grammatikkoden kvar ("3 |4Charge:Charges;"), tooltipen visar den upplöst ("3 Charges").
local function ResolvePlural(s)
	return (s:gsub("([%d%.,]+)(%s*)|4([^:;]*):([^;]*);", function(n, sp, one, many)
		return n .. sp .. (tonumber((n:gsub(",", ""))) == 1 and one or many)
	end))
end

-- Tooltips vars rader den här filen har översatt. UI.lua hoppar över dem; töms när tooltipen töms.
WPS.tooltipHandled = setmetatable({}, { __mode = "k" })

local function TranslateDataLines(tooltip, data)
	WPS.tooltipHandled[tooltip] = true
	local translate = WPS.UITranslate
	local lines = data and data.lines
	if not (translate and lines and WPS.On("ui")) then return end
	local own = {}
	for _, line in ipairs(lines) do
		for _, field in ipairs({ "leftText", "rightText" }) do
			local text = line[field]
			if type(text) == "string" and text ~= "" and not isSecret(text) then
				own[ResolvePlural(text)] = true
			end
		end
	end
	local name = tooltip:GetName()
	for i = 1, tooltip:NumLines() do
		-- Rad 1 vänster är namnet; det sköts med id eller namnuppslag.
		for _, side in ipairs(i == 1 and { "Right" } or { "Left", "Right" }) do
			local fs = _G[name .. "Text" .. side .. i]
			local text = fs and fs:GetText()
			if text and not isSecret(text) and own[text] then
				local sv = translate(text)
				if sv and sv ~= text then fs:SetText(sv) end
			end
		end
	end
end

---------------------------------------------------------------------------
-- Items
---------------------------------------------------------------------------

local function OnItem(tooltip, data)
	if not (data and data.id) then return "skip:no-id" end
	if not Active("item") then return "skip:inactive(on=" .. tostring(WPS.On("item")) .. ")" end
	local name = tooltip.GetName and tooltip:GetName()
	local line1 = name and _G[name .. "TextLeft1"]
	if not line1 then return "skip:no-line1" end
	pcall(TranslateDataLines, tooltip, data)
	local t = WPS.L.item[data.id]
	if not t then
		-- Föremål utan egen post i Item.lua: använd namnuppslaget direkt, av samma skäl som ovan.
		local sv = WPS.Name(line1:GetText())
		if sv then
			line1:SetText(sv)
			return "name-fallback"
		end
		return "skip:no-translation"
	end

	local english = line1:GetText()
	if t.n and english and english ~= t.n then
		line1:SetText(t.n)
		-- Grå rad med originalnamn skapat genom AddLine() taintar oss.
		-- För nu visar tooltips bara svenska namn; du kan se engelska med Alt.
	end

	if t.d and t.h then
		local fs, pre, post = FindLine(tooltip, function(text) return WPS.Hash(text) == t.h end)
		if fs then fs:SetText(pre .. t.d .. post) end
	end
	tooltip:Show()
	return "done"
end

---------------------------------------------------------------------------
-- Spells
---------------------------------------------------------------------------

local function OnSpell(tooltip, data)
	if not (data and data.id and Active("spell")) then return end
	pcall(TranslateDataLines, tooltip, data)
	local t = WPS.L.spell[data.id]
	if not t then return end
	local name = tooltip.GetName and tooltip:GetName()
	local line1 = name and _G[name .. "TextLeft1"]
	if not line1 then return end

	if t.n then line1:SetText(t.n) end

	if t.d and C_Spell and C_Spell.GetSpellDescription then
		local resolved = Norm(C_Spell.GetSpellDescription(data.id))
		if resolved ~= "" then
			local fs = FindLine(tooltip, function(text) return text == resolved end)
			if fs then
				local sv = WPS.Resolve(t.e or resolved, t.d, resolved)
				if sv then fs:SetText(sv) end
			end
		end
	end
	tooltip:Show()
end

---------------------------------------------------------------------------
-- Buffar och debuffar
---------------------------------------------------------------------------

local function OnAura(tooltip, data)
	if not (data and data.id and Active("spell")) then return end
	local t = WPS.L.spell[data.id]
	if not t then return end
	local name = tooltip.GetName and tooltip:GetName()
	local line1 = name and _G[name .. "TextLeft1"]
	if not line1 then return end

	if t.n then line1:SetText(t.n) end

	if t.a and t.ea then
		local sv
		local fs = FindLine(tooltip, function(text)
			if t.ea:find("$", 1, true) then
				sv = WPS.Resolve(t.ea, t.a, text)
			elseif text == t.ea then
				sv = t.a
			end
			return sv ~= nil
		end)
		if fs then fs:SetText(sv) end
	end
	tooltip:Show()
end

---------------------------------------------------------------------------
-- NPC:er (muspekaren över en varelse)
---------------------------------------------------------------------------

local function OnUnit(tooltip, data)
	if not (data and data.guid and Active("npc")) then return end
	local unitType, id = data.guid:match("^(%a+)%-%d+%-%d+%-%d+%-%d+%-(%d+)")
	local isNpc = unitType == "Creature" or unitType == "Vehicle"
	local sv = isNpc and WPS.L.npc[tonumber(id)]
	local name = tooltip.GetName and tooltip:GetName()
	local line1 = name and _G[name .. "TextLeft1"]
	if sv and line1 then
		line1:SetText(sv)
	end
	-- Övriga rader: NPC-titel (<Innkeeper>), nivå och typ (Level 26, Beast), Skinnable, uppdrag och
	-- målrader (5/8 Dragonmaw War Banner). Samma uppslag som gränssnittet (UI.lua).
	local translate = WPS.UITranslate
	if translate and name then
		for i = 2, tooltip:NumLines() do
			local fs = _G[name .. "TextLeft" .. i]
			local text = fs and fs:GetText()
			if text and not isSecret(text) and text ~= "" then
				local t = translate(text)
				if t and t ~= text then fs:SetText(t) end
			end
		end
	end
	tooltip:Show()
end

-- Klienten kan lämna ut "hemliga" värden (t.ex. auror i instanser) som kastar fel vid
-- första jämförelsen. Då låter vi tooltipen vara engelsk i stället för att visa ett Lua-fel.
local KIND = { [OnItem] = "item", [OnSpell] = "spell", [OnAura] = "aura", [OnUnit] = "unit" }

local function Snapshot(tooltip, data, kind)
	if tooltip ~= GameTooltip and tooltip ~= ItemRefTooltip then return end
	local name, lines = tooltip:GetName(), {}
	for i = 1, math.min(tooltip:NumLines(), 10) do
		local fs = _G[name .. "TextLeft" .. i]
		local text = fs and fs:GetText()
		if text and text ~= "" then lines[#lines + 1] = text end
	end
	WPS.Remember("tooltip", { kind = kind, id = data and data.id, guid = data and data.guid, lines = lines })
end

-- Felsökning: jämför data.lines (raderna Blizzard byggde tooltipen av) med tooltipens rader.
-- Hela listan loggas första gången per id och session; därefter bara antal och avvikelser.
local dlSeen = {}
local function LogDataLines(tooltip, data, kind)
	local name = tooltip:GetName()
	local lines = data and data.lines
	local key = kind .. ":" .. Show(data and (data.id or data.guid))
	WPS.TipLog("dlines", key, "data.lines=" .. (lines and #lines or "nil"), "tooltip=" .. tooltip:NumLines())
	if not lines then return end
	local full = not dlSeen[key]
	dlSeen[key] = true
	for i, line in ipairs(lines) do
		for _, side in ipairs({ "Left", "Right" }) do
			local field = side == "Left" and "leftText" or "rightText"
			local en = line[field]
			local fs = _G[name .. "Text" .. side .. i]
			local tt = fs and fs:IsShown() and fs:GetText() or nil
			if tt == "" then tt = nil end
			if en == "" then en = nil end
			local same = en == tt
			if full or not same then
				WPS.TipLog("dline", key, i .. side:sub(1, 1), "type=" .. Show(line.type), same and "same" or "DIFF",
					"data=" .. Show(en), "tooltip=" .. Show(tt))
			end
		end
	end
end

local function Safe(fn)
	local kind = KIND[fn]
	return function(tooltip, data)
		local dbg = WPS.db and WPS.db.tipDebug and (tooltip == GameTooltip or tooltip == ItemRefTooltip)
		local before = dbg and Line1(tooltip)
		local ok, res = pcall(fn, tooltip, data)
		if dbg then
			WPS.TipLog("post", kind, tooltip:GetName(), "id=" .. Show(data and data.id), "type=" .. Show(data and data.type),
				"alt=" .. Show(IsAltKeyDown()), ok and Show(res or "-") or ("ERROR:" .. Show(res)),
				"|", before, "->", Line1(tooltip))
		end
		if dbg then pcall(LogDataLines, tooltip, data, kind) end
		pcall(Snapshot, tooltip, data, kind)
	end
end

WPS.OnLogin(function()
	local ok = TooltipDataProcessor and TooltipDataProcessor.AddTooltipPostCall and Enum and Enum.TooltipDataType
	WPS.hooks["TooltipDataProcessor"] = ok and true or false
	if not ok then return end
	local types = Enum.TooltipDataType
	TooltipDataProcessor.AddTooltipPostCall(types.Item, Safe(OnItem))
	TooltipDataProcessor.AddTooltipPostCall(types.Spell, Safe(OnSpell))
	if types.UnitAura then TooltipDataProcessor.AddTooltipPostCall(types.UnitAura, Safe(OnAura)) end
	if types.Unit then TooltipDataProcessor.AddTooltipPostCall(types.Unit, Safe(OnUnit)) end
	WPS.hooks["Tooltip: buffar (UnitAura)"] = types.UnitAura ~= nil

	-- Felsökning: loggar varje bildruta där GameTooltip visas/döljs eller någon rad (vänster L, höger R)
	-- ändrar text. Bara raderna som ändrats loggas, med radnummer.
	local prev, wasShown = {}, false
	local function Clip(v)
		if v == nil then return "<none>" end
		return (Show(v):gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):gsub("\n", "\\n"):sub(1, 40))
	end
	CreateFrame("Frame"):SetScript("OnUpdate", function()
		if not (WPS.db and WPS.db.tipDebug) then return end
		local shown = GameTooltip:IsShown()
		if shown ~= wasShown then
			WPS.TipLog("frame", shown and "shown" or "hidden")
			wasShown = shown
			if not shown then prev = {} return end
		end
		if not shown then return end
		local cur = {}
		for i = 1, math.min(GameTooltip:NumLines(), 25) do
			for _, side in ipairs({ "L", "R" }) do
				local fs = _G["GameTooltipText" .. (side == "L" and "Left" or "Right") .. i]
				local text = fs and fs:IsShown() and fs:GetText() or nil
				if text == "" then text = nil end
				cur[side .. i] = text
			end
		end
		for i = 1, 25 do
			for _, side in ipairs({ "L", "R" }) do
				local k = side .. i
				if cur[k] ~= prev[k] then
					WPS.TipLog("frame", k, Clip(prev[k]), "->", Clip(cur[k]))
				end
			end
		end
		prev = cur
	end)

	-- Flaggan från TranslateDataLines gäller bara innehållet den sattes för.
	for _, tip in ipairs({ GameTooltip, ItemRefTooltip }) do
		if tip and tip.HookScript then
			local clear = function(self) WPS.tooltipHandled[self] = nil end
			pcall(tip.HookScript, tip, "OnTooltipCleared", clear)
			pcall(tip.HookScript, tip, "OnHide", clear)
		end
	end

	-- Alt tryckt/släppt medan tooltipen visas: bygg om den.
	local f = CreateFrame("Frame")
	f:RegisterEvent("MODIFIER_STATE_CHANGED")
	f:SetScript("OnEvent", function(_, _, key)
		if (key == "LALT" or key == "RALT") and GameTooltip:IsShown() and GameTooltip.RefreshData then
			GameTooltip:RefreshData()
		end
	end)
end)
