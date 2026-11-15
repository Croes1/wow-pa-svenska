-- NPC-dialog: gossipfönstrets hälsning och alternativ, samt questgivarnas hälsning (QUEST_GREETING).
-- Texterna slås upp på samma nyckel som collectorn sparar: "<längd>_<djb2 i hex>" av texten
-- med spelarens namn ersatt av $N. Bara efterhand-ändring av FontStrings, inga ersatta funktioner.

local _, WPS = ...

local function Key(s)
	local h = 5381
	for i = 1, #s do
		h = (h * 33 + s:byte(i)) % 4294967296
	end
	return ("%d_%08x"):format(#s, h)
end

local function EscapePattern(s)
	return (s:gsub("[%^%$%(%)%%%.%[%]%*%+%-%?]", "%%%0"))
end

-- Engelsk text som den visas -> svensk text, eller nil.
local function Lookup(text)
	if type(text) ~= "string" or text == "" then return end
	local norm = text:gsub("\r\n", "\n")
	local name = UnitName("player")
	if name then norm = norm:gsub(EscapePattern(name), "$N") end
	local sv = WPS.L.gossip[Key(norm)]
	return sv and WPS.Expand(sv)
end

local seen -- rader i det fönster som visas just nu, för /wps fel

local function Translate(fs)
	if not (fs and fs.GetText and fs.SetText) then return end
	local en = fs:GetText()
	local sv = Lookup(en)
	if sv then fs:SetText(sv) end
	if seen and type(en) == "string" and en ~= "" then
		local norm = en:gsub("\r\n", "\n")
		local name = UnitName("player")
		if name then norm = norm:gsub(EscapePattern(name), "$N") end
		seen[#seen + 1] = { key = Key(norm), en = en, sv = sv }
	end
end

---------------------------------------------------------------------------
-- Gossipfönstret (retail-likt: rader i en ScrollBox)
---------------------------------------------------------------------------

local function GossipBox()
	local panel = GossipFrame and (GossipFrame.GreetingPanel or GossipFrame)
	return panel and panel.ScrollBox
end

local function TranslateRow(row)
	Translate(row.GreetingText)
	-- Alternativknappar: texten ligger på knappen själv eller i en FontString.
	if row.GetFontString and row:GetFontString() then
		local fs = row:GetFontString()
		local before = fs:GetText()
		Translate(fs)
		if fs:GetText() ~= before and row.Resize then pcall(row.Resize, row) end
	end
	if row.Text ~= (row.GetFontString and row:GetFontString()) then Translate(row.Text) end
end

local function ApplyGossip()
	if not WPS.On("gossip") then return end
	seen = {}
	local box = GossipBox()
	if box and box.ForEachFrame then
		box:ForEachFrame(function(row) pcall(TranslateRow, row) end)
	end
	-- Äldre layout
	Translate(GossipGreetingText)
	WPS.Remember("gossip", { npc = UnitName("npc"), lines = seen })
	seen = nil
end

local function ApplyGreeting()
	if not WPS.On("gossip") then return end
	seen = {}
	Translate(GreetingText or (QuestFrameGreetingPanel and QuestFrameGreetingPanel.GreetingText))
	WPS.Remember("gossip", { npc = UnitName("npc"), lines = seen })
	seen = nil
end

WPS.OnLogin(function()
	local f = CreateFrame("Frame")
	f:RegisterEvent("GOSSIP_SHOW")
	f:RegisterEvent("QUEST_GREETING")
	f:SetScript("OnEvent", function(_, event)
		-- Vänta en bildruta så att Blizzard hunnit fylla fönstret.
		C_Timer.After(0, event == "GOSSIP_SHOW" and ApplyGossip or ApplyGreeting)
	end)
	WPS.hooks["Gossip-händelser"] = true

	local box = GossipBox()
	if box and box.RegisterCallback then
		local ok = pcall(box.RegisterCallback, box, "OnDataRangeChanged", ApplyGossip, WPS)
		WPS.hooks["Gossip ScrollBox"] = ok
	end
end)
