-- Inställningar: /wps och en panel under Alternativ > AddOns.

local _, WPS = ...

local function Status()
	WPS.Print("Inställningar (ändra med |cffffff00/wps <namn> on|off|r):")
	for _, c in ipairs(WPS.CATEGORIES) do
		WPS.Print(("  %s: %s – %s"):format(c.key, WPS.db[c.key] and "|cff00ff00på|r" or "|cffff4444av|r", c.label))
	end
	WPS.Print("Kommandon: /wps (öppna panelen), /wps orig (växla original/svenska), /wps diag, /wps status, /wps fel <kommentar>, /wps dump (samla engelska texter)")
	WPS.Print("Tips: håll Alt över en tooltip för engelskan. Bind en tangent under Alternativ > Tangentbindningar > AddOns.")
end

local function Count(t)
	local n = 0
	for _ in pairs(t) do n = n + 1 end
	return n
end

local function Diag()
	local version, build, _, toc = GetBuildInfo()
	WPS.Print("Build", version, build, "Interface", toc)
	WPS.Print(("Data: %d quests, %d items, %d spells"):format(Count(WPS.L.quest), Count(WPS.L.item), Count(WPS.L.spell)))
	local names = {}
	for name in pairs(WPS.hooks) do names[#names + 1] = name end
	table.sort(names)
	for _, name in ipairs(names) do
		local state = WPS.hooks[name]
		local label = state == "väntar" and "|cffffff00VÄNTAR|r" or state and "|cff00ff00OK|r     " or "|cffff4444SAKNAS|r"
		WPS.Print(("  %s %s"):format(label, name))
	end
	if WPS.hooks["QuestLog ScrollBox"] == "väntar" then
		WPS.Print("  (ScrollBox kopplas in första gången du öppnar questloggen/kartan)")
	end
	if WPS.scrollBoxPath then WPS.Print("  ScrollBox:", WPS.scrollBoxPath) end
	if WPS.hookErr then WPS.Print("  orsak:", WPS.hookErr) end
end

---------------------------------------------------------------------------
-- /wps fel: spelaren rapporterar en översättning som blev fel i spelet.
-- Sparar det som senast visades (WPS.last) med kommentaren i WPSDB.reports.
-- pipeline/vak.py feedback läser rapporterna och listar dem för översättaren.
---------------------------------------------------------------------------

local function CopyTable(t)
	if type(t) ~= "table" then return t end
	local out = {}
	for k, v in pairs(t) do out[k] = CopyTable(v) end
	return out
end

local SLOT_LABEL = { tooltip = "tooltip", castbar = "castbar", gossip = "dialog", chat = "chatt", quest = "quest" }

local function Describe(slot, d)
	if slot == "tooltip" then
		return ("%s %s: %s"):format(d.kind or "?", tostring(d.id or d.guid or ""), d.lines and d.lines[1] or "")
	elseif slot == "castbar" then
		return ("spell %s: %s"):format(tostring(d.id), d.sv or d.en or "")
	elseif slot == "gossip" then
		return ("%s, %d rader"):format(d.npc or "NPC", d.lines and #d.lines or 0)
	elseif slot == "chat" then
		local first = d.lines and d.lines[1]
		return first and (first.sv or first.en) or ""
	elseif slot == "quest" then
		return ("quest %s"):format(tostring(d.id))
	end
	return ""
end

local function Report(comment)
	WPS.db.reports = WPS.db.reports or {}
	local now, last = time(), {}
	-- Bara det som visats de senaste fem minuterna; äldre är troligen inte det som avses.
	for slot, d in pairs(WPS.last) do
		if d.at and now - d.at <= 300 then last[slot] = CopyTable(d) end
	end
	local r = {
		at = now, date = date("%Y-%m-%d %H:%M"), comment = comment,
		zone = GetZoneText(), subzone = GetSubZoneText(), last = last,
	}
	table.insert(WPS.db.reports, r)
	WPS.Print(("Rapport #%d sparad: \"%s\""):format(#WPS.db.reports, comment))
	local newest, newestAt = nil, 0
	for slot, d in pairs(last) do
		WPS.Print(("  %s: %s"):format(SLOT_LABEL[slot] or slot, Describe(slot, d)))
		if d.at > newestAt then newest, newestAt = slot, d.at end
	end
	if not next(last) then
		WPS.Print("  (inget visat de senaste 5 minuterna – beskriv var felet syns i kommentaren)")
	elseif newest then
		WPS.Print(("  Senast visat: %s. Sparas till disk vid /reload eller utloggning."):format(SLOT_LABEL[newest] or newest))
	end
end

local function Feedback(rest)
	local cmd = rest:lower()
	WPS.db.reports = WPS.db.reports or {}
	if rest == "" then
		WPS.Print("Användning: |cffffff00/wps fel <vad som är fel>|r, t.ex. /wps fel borde vara \"Flår\"")
		WPS.Print("Sparar det som senast visades (tooltip, castbar, dialog, chatt, quest). Även: /wps fel lista, /wps fel ångra")
	elseif cmd == "lista" then
		if #WPS.db.reports == 0 then WPS.Print("Inga rapporter.") end
		for i, r in ipairs(WPS.db.reports) do
			WPS.Print(("#%d %s %s: %s"):format(i, r.date or "", r.zone or "", r.comment or ""))
		end
	elseif cmd == "ångra" or cmd == "angra" then
		local r = table.remove(WPS.db.reports)
		WPS.Print(r and ("Tog bort rapporten \"%s\"."):format(r.comment or "") or "Inga rapporter att ta bort.")
	else
		Report(rest)
	end
end

local panel
local boxes = {}

local function RefreshPanel()
	for key, cb in pairs(boxes) do cb:SetChecked(WPS.db[key] and true or false) end
end

local function SetAll(on)
	for _, c in ipairs(WPS.CATEGORIES) do WPS.db[c.key] = on end
	RefreshPanel()
end

local function Button(parent, text, width, onClick)
	local b = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
	b:SetSize(width, 22)
	b:SetText(text)
	b:SetScript("OnClick", onClick)
	return b
end

local function BuildPanel()
	panel = CreateFrame("Frame")
	panel.name = "Wow på Svenska"

	local title = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
	title:SetPoint("TOPLEFT", 16, -16)
	title:SetText("Wow på Svenska")

	local intro = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
	intro:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -6)
	intro:SetJustifyH("LEFT")
	intro:SetText("Välj vad som ska visas på svenska. Det du kryssar ur visas på engelska.")

	local y, group = -64, nil
	for _, c in ipairs(WPS.CATEGORIES) do
		if c.group ~= group then
			group = c.group
			if y < -64 then y = y - 8 end
			local head = panel:CreateFontString(nil, "ARTWORK", "GameFontNormal")
			head:SetPoint("TOPLEFT", 16, y)
			head:SetText(group)
			y = y - 20
		end
		local cb = CreateFrame("CheckButton", nil, panel, "UICheckButtonTemplate")
		cb:SetPoint("TOPLEFT", 20, y)
		cb:SetScript("OnClick", function(self) WPS.db[c.key] = self:GetChecked() and true or false end)
		boxes[c.key] = cb
		local label = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
		label:SetPoint("TOPLEFT", cb, "TOPRIGHT", 4, -3)
		label:SetText(c.label)
		local desc = panel:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
		desc:SetPoint("TOPLEFT", label, "BOTTOMLEFT", 0, -2)
		desc:SetText(c.desc or "")
		y = y - 38
	end

	local on = Button(panel, "Allt på", 100, function() SetAll(true) end)
	on:SetPoint("TOPLEFT", 20, y - 8)
	local off = Button(panel, "Allt av", 100, function() SetAll(false) end)
	off:SetPoint("LEFT", on, "RIGHT", 8, 0)
	local reload = Button(panel, "Ladda om gränssnittet", 180, function() ReloadUI() end)
	reload:SetPoint("LEFT", off, "RIGHT", 8, 0)

	local hint = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
	hint:SetPoint("TOPLEFT", on, "BOTTOMLEFT", 0, -12)
	hint:SetJustifyH("LEFT")
	hint:SetText("Ändringar gäller nästa gång ett fönster eller en tooltip öppnas. Text som redan visas byts\n" ..
		"tillbaka först när du laddar om gränssnittet.\n\n" ..
		"Håll Alt över en tooltip för att se engelskan. Bind en tangent för att växla all text under\n" ..
		"Tangentbindningar > AddOns. Kommandon: /wps (den här panelen), /wps status, /wps fel <kommentar>.")

	panel:SetScript("OnShow", RefreshPanel)
	RefreshPanel()

	if Settings and Settings.RegisterCanvasLayoutCategory then
		WPS.category = Settings.RegisterCanvasLayoutCategory(panel, panel.name)
		Settings.RegisterAddOnCategory(WPS.category)
	end
end

WPS.OnLogin(function()
	pcall(BuildPanel)
end)

-- /wps dump: samla engelska gränssnittstexter som syns just nu (se UI.lua,
-- WPS.UIDump). Material för en uppdateringsrunda; hamnar i WPSDB.uiDump.
local function Dump(arg)
	if not WPS.UIDump then
		WPS.Print("dump: UI.lua saknar kommandot (för gammal kopia på disk?).")
		return
	end
	WPS.UIDump(arg)
end

SLASH_WPS1 = "/wps"
SlashCmdList.WPS = function(msg)
	if not WPS.db then return end
	-- /wps fel behåller kommentarens versaler, därför före lower().
	local first, rest = (msg or ""):match("^%s*(%S+)%s*(.-)%s*$")
	if first and first:lower() == "fel" then return Feedback(rest) end
	local cmd, arg = (msg or ""):lower():match("^%s*(%S*)%s*(%S*)")
	if cmd == "" then
		if WPS.category and Settings and Settings.OpenToCategory then
			Settings.OpenToCategory(WPS.category:GetID())
		else
			Status()
		end
	elseif cmd == "status" or cmd == "help" then
		Status()
	elseif cmd == "orig" or cmd == "original" then
		WPS.Toggle()
	elseif cmd == "diag" then
		Diag()
	elseif cmd == "dump" then
		Dump(arg)
	elseif WPS.db[cmd] ~= nil then
		if arg == "on" or arg == "off" then
			WPS.db[cmd] = arg == "on"
		else
			WPS.db[cmd] = not WPS.db[cmd]
		end
		WPS.Print(cmd, WPS.db[cmd] and "|cff00ff00på|r" or "|cffff4444av|r")
		RefreshPanel()
	else
		Status()
	end
end
