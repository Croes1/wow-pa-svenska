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
-- Items
---------------------------------------------------------------------------

local function OnItem(tooltip, data)
	if not (data and data.id and Active("item")) then return end
	local t = WPS.L.item[data.id]
	if not t then return end
	local name = tooltip.GetName and tooltip:GetName()
	local line1 = name and _G[name .. "TextLeft1"]
	if not line1 then return end

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
end

---------------------------------------------------------------------------
-- Spells
---------------------------------------------------------------------------

local function OnSpell(tooltip, data)
	if not (data and data.id and Active("spell")) then return end
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

local function Safe(fn)
	local kind = KIND[fn]
	return function(tooltip, data)
		pcall(fn, tooltip, data)
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

	-- Alt tryckt/släppt medan tooltipen visas: bygg om den.
	local f = CreateFrame("Frame")
	f:RegisterEvent("MODIFIER_STATE_CHANGED")
	f:SetScript("OnEvent", function(_, _, key)
		if (key == "LALT" or key == "RALT") and GameTooltip:IsShown() and GameTooltip.RefreshData then
			GameTooltip:RefreshData()
		end
	end)
end)
