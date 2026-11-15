-- Quests: questfönster (NPC-dialog), questlogg och questtracker.
-- Allt görs i efterhand med hooksecurefunc/HookScript: Blizzard sätter engelsk text först,
-- därefter byter vi ut den. Saknas översättning rörs ingenting.

local _, WPS = ...
local L = WPS.L.quest

local function Get(id)
	if type(id) ~= "number" or id <= 0 then return nil end
	return L[id]
end

local function SetText(fs, text)
	if fs and text and fs.SetText and fs:IsShown() then
		fs:SetText(WPS.Expand(text))
	end
end

-- Målrad: "#/# Murlocfena" + engelsk rad "3/10 Murloc Fin" -> "3/10 Murlocfena".
local function ObjectiveLine(q, index, english)
	local tl = q.l and q.l[index]
	if not tl or type(english) ~= "string" then return nil end
	local a, b = english:match("(%d+)%s*/%s*(%d+)")
	local hasProgress = tl:find("#/#", 1, true) ~= nil
	if (a ~= nil) ~= hasProgress then return nil end
	if a then tl = tl:gsub("#/#", a .. "/" .. b) end
	return tl
end

---------------------------------------------------------------------------
-- Questfönster och detaljvyn i questloggen (delar QuestInfo)
---------------------------------------------------------------------------

local function CurrentQuestID()
	if QuestInfoFrame and QuestInfoFrame.questLog then
		return C_QuestLog.GetSelectedQuest and C_QuestLog.GetSelectedQuest()
	end
	return GetQuestID and GetQuestID()
end

local function ApplyQuestInfo()
	if not WPS.On("quest") then return end
	local id = CurrentQuestID()
	WPS.Remember("quest", { id = id, en = QuestInfoTitleHeader and QuestInfoTitleHeader:GetText(), translated = Get(id) ~= nil })
	local q = Get(id)
	if not q then return end
	SetText(QuestInfoTitleHeader, q.t)
	SetText(QuestInfoDescriptionText, q.d)
	SetText(QuestInfoObjectivesText, q.o)
	SetText(QuestInfoRewardText, q.c)

	if q.l and QuestInfoFrame and QuestInfoFrame.questLog and C_QuestLog.GetQuestObjectives then
		local objectives = C_QuestLog.GetQuestObjectives(CurrentQuestID())
		for i = 1, #(objectives or {}) do
			local fs = _G["QuestInfoObjective" .. i]
			local text = fs and fs:IsShown() and ObjectiveLine(q, i, objectives[i].text)
			if text then fs:SetText(text) end
		end
	end
end

local function ApplyDialog()
	if not WPS.On("quest") then return end
	local id = GetQuestID and GetQuestID()
	WPS.Remember("quest", { id = id, translated = Get(id) ~= nil })
	local q = Get(id)
	if not q then return end
	SetText(QuestProgressTitleText, q.t)
	SetText(QuestProgressText, q.p)
	SetText(QuestInfoTitleHeader, q.t)
	SetText(QuestInfoRewardText, q.c)
end

---------------------------------------------------------------------------
-- Questlogg: listan till vänster
---------------------------------------------------------------------------

local function TranslateLogButton(button)
	local id = button.questID
	if not id and button.GetElementData then
		local data = button:GetElementData()
		id = data and (data.questID or (data.info and data.info.questID))
	end
	local q = Get(id)
	local fs = button.Text or button.text
	if not (q and q.t and fs and fs.GetText) then return end
	local current = fs:GetText()
	if not current then return end
	local prefix = current:match("^(%[%d+[%+%-]?%a*%]%s*)") or "" -- "[12] " framför titeln
	fs:SetText(prefix .. q.t)
end

local function FindLogBox()
	local candidates = {
		QuestMapFrame and QuestMapFrame.QuestsFrame and QuestMapFrame.QuestsFrame.ScrollBox,
		QuestScrollFrame and QuestScrollFrame.ScrollBox,
		QuestLogFrame and QuestLogFrame.ScrollBox,
	}
	for _, box in pairs(candidates) do
		if type(box) == "table" and box.ForEachFrame then return box end
	end
	-- Okänd struktur i denna klient: sök bland questkartans underobjekt efter en ScrollBox.
	local seen = {}
	local function Search(obj, depth, path)
		if type(obj) ~= "table" or seen[obj] or depth > 4 then return end
		seen[obj] = true
		if obj.ForEachFrame and obj.RegisterCallback then return obj, path end
		for key, child in pairs(obj) do
			if type(key) == "string" and type(child) == "table" and child ~= obj then
				local box, where = Search(child, depth + 1, path .. "." .. key)
				if box then return box, where end
			end
		end
	end
	for _, root in ipairs({ "QuestMapFrame", "QuestScrollFrame" }) do
		local box, where = Search(_G[root], 0, root)
		if box then return box, where end
	end
end

local function ApplyQuestLogList()
	if not WPS.On("quest") then return end
	local box = FindLogBox()
	if box then box:ForEachFrame(TranslateLogButton) end
end

---------------------------------------------------------------------------
-- Questtracker
---------------------------------------------------------------------------

local function TranslateBlock(block)
	local q = Get(block.id or block.questID)
	if not q then return end
	local header = block.HeaderText or block.headerText
	if q.t and header and header.SetText then header:SetText(q.t) end

	local lines = block.usedLines or block.lines
	if q.l and lines then
		for key, line in pairs(lines) do
			local fs = type(line) == "table" and (line.Text or line.text)
			if type(key) == "number" and fs and fs.GetText then
				local text = ObjectiveLine(q, key, fs:GetText())
				if text then fs:SetText(text) end
			end
		end
	end
end

local function ApplyTracker()
	if not WPS.On("quest") then return end
	local module = QuestObjectiveTracker
	if not (module and module.usedBlocks) then return end
	for _, blocks in pairs(module.usedBlocks) do
		for _, block in pairs(blocks) do
			TranslateBlock(block)
		end
	end
end

---------------------------------------------------------------------------
-- Koppla in hookarna
---------------------------------------------------------------------------

local function Hook(name, target, method, fn)
	local ok = pcall(function()
		if method then
			hooksecurefunc(target, method, fn)
		else
			hooksecurefunc(name, fn)
		end
	end)
	WPS.hooks[name] = ok
end

local function HookShow(name, frame, fn)
	local ok = frame and pcall(frame.HookScript, frame, "OnShow", fn)
	WPS.hooks[name] = ok and true or false
end

WPS.OnLogin(function()
	Hook("QuestInfo_Display", nil, nil, ApplyQuestInfo)
	Hook("QuestLogQuests_Update", nil, nil, ApplyQuestLogList)

	-- Rullar man i listan återanvänds knapparna, så vi lyssnar också på ScrollBox.
	-- Rutan kan skapas först när questkartan öppnas, så vi provar igen då.
	local registered, mapOpened = false, false
	local function RegisterScroll()
		if registered then return end
		local box, where = FindLogBox()
		if not (box and box.RegisterCallback) then
			WPS.hookErr = mapOpened and "ingen ScrollBox hittades under QuestMapFrame/QuestScrollFrame" or nil
			WPS.hooks["QuestLog ScrollBox"] = mapOpened and false or "väntar"
			return
		end
		WPS.scrollBoxPath = where
		local ok, err = pcall(function()
			box:RegisterCallback("OnUpdate", ApplyQuestLogList, WPS)
			box:RegisterCallback("OnDataRangeChanged", ApplyQuestLogList, WPS)
		end)
		registered = ok
		WPS.hooks["QuestLog ScrollBox"] = ok
		WPS.hookErr = not ok and tostring(err) or nil
	end
	RegisterScroll()
	if QuestMapFrame and QuestMapFrame.HookScript then
		pcall(QuestMapFrame.HookScript, QuestMapFrame, "OnShow", function()
			mapOpened = true
			RegisterScroll()
			C_Timer.After(0, ApplyQuestLogList)
		end)
	end

	if QuestObjectiveTracker then
		Hook("QuestObjectiveTracker:Update", QuestObjectiveTracker, "Update", ApplyTracker)
		Hook("QuestObjectiveTracker:UpdateSingle", QuestObjectiveTracker, "UpdateSingle", ApplyTracker)
		Hook("QuestObjectiveTracker:EndLayout", QuestObjectiveTracker, "EndLayout", ApplyTracker)
	else
		WPS.hooks["QuestObjectiveTracker"] = false
	end

	HookShow("QuestFrameProgressPanel", QuestFrameProgressPanel, function() C_Timer.After(0, ApplyDialog) end)
	HookShow("QuestFrameRewardPanel", QuestFrameRewardPanel, function() C_Timer.After(0, ApplyDialog) end)

	local events = CreateFrame("Frame")
	for _, e in ipairs({ "QUEST_PROGRESS", "QUEST_COMPLETE" }) do pcall(events.RegisterEvent, events, e) end
	events:SetScript("OnEvent", function() C_Timer.After(0, ApplyDialog) end)
	WPS.hooks["Quest-händelser"] = true
end)
