-- Castbars, namn på enhetsramar/namnplattor och zonnamn.
-- Bara HookScript/hooksecurefunc. Vi skriver om text i FontStrings efter att Blizzard satt den;
-- FontStrings är inte skyddade, så det påverkar inte secure-kod.
-- Allt körs i pcall: klienten kan lämna ut "hemliga" värden (t.ex. i instanser).

local _, WPS = ...

local isSecret = issecretvalue or function() return false end

-- Castbaren visar en pågående handling: castbar-formen (c, t.ex. "Flår") går före namnet (n, "Flåning").
local function CastName(id)
	local t = id and WPS.L.spell[id]
	return t and (t.c or t.n)
end

local function NpcName(unit)
	local guid = UnitGUID(unit)
	if not guid or isSecret(guid) then return end
	local unitType, id = guid:match("^(%a+)%-%d+%-%d+%-%d+%-%d+%-(%d+)")
	if unitType == "Creature" or unitType == "Vehicle" then
		return WPS.L.npc[tonumber(id)]
	end
end

---------------------------------------------------------------------------
-- Castbars
---------------------------------------------------------------------------

local function BarText(bar)
	return bar.Text or bar.text or (bar.GetName and bar:GetName() and _G[bar:GetName() .. "Text"])
end

-- Läser vad enheten kastar just nu och byter bara texten om den är det engelska
-- spellnamnet, så att "Interrupted"/"Failed" och andra addons text lämnas i fred.
local function UpdateBar(bar)
	if not WPS.On("spell") then return end
	local unit = bar.unit
	local fs = BarText(bar)
	if not (unit and fs and bar:IsShown()) then return end
	local name, text, _, _, _, _, _, _, spellID = UnitCastingInfo(unit)
	if not name then
		local _
		name, text, _, _, _, _, _, spellID = UnitChannelInfo(unit)
	end
	if not name or isSecret(name) or isSecret(spellID) then return end
	local sv = CastName(spellID)
	local shown = fs:GetText()
	if sv and (shown == name or shown == text) then fs:SetText(sv) end
	if unit == "player" or unit == "pet" then
		WPS.Remember("castbar", { id = spellID, en = text or name, sv = fs:GetText() })
	end
end

local hookedBars = {}
local function HookBar(bar, label)
	if not bar or hookedBars[bar] or not bar.HookScript then return false end
	hookedBars[bar] = true
	bar:HookScript("OnEvent", function(self) pcall(UpdateBar, self) end)
	bar:HookScript("OnShow", function(self) pcall(UpdateBar, self) end)
	if label then WPS.hooks["Castbar: " .. label] = true end
	return true
end

local function HookNamePlateBar(unit)
	local plate = C_NamePlate and C_NamePlate.GetNamePlateForUnit and C_NamePlate.GetNamePlateForUnit(unit)
	local uf = plate and plate.UnitFrame
	if uf then HookBar(uf.castBar or uf.CastBar) end
end

---------------------------------------------------------------------------
-- Namn på målram, fokus och namnplattor
---------------------------------------------------------------------------

local function UpdateUnitName(frame)
	if not WPS.On("npc") then return end
	local unit = frame.unit or frame.displayedUnit
	local fs = frame.name or frame.Name
	if not (unit and fs and fs.SetText) or isSecret(unit) then return end
	local sv = NpcName(unit)
	if sv then fs:SetText(sv) end
end

local function UpdateTargetNames()
	for _, f in ipairs({ TargetFrame, FocusFrame, TargetFrameToT, FocusFrameToT }) do
		if f then
			-- Retail-lik ram: namnet ligger djupare än f.name.
			local content = f.TargetFrameContent and f.TargetFrameContent.TargetFrameContentMain
			local fs = f.name or (content and content.Name)
			if fs and f.unit then pcall(UpdateUnitName, { unit = f.unit, name = fs }) end
		end
	end
end

---------------------------------------------------------------------------
-- Zonnamn (stor text vid områdesbyte, minikartan)
---------------------------------------------------------------------------

local busy = {}
local function HookZoneString(fs, label)
	if not (fs and fs.SetText) then return false end
	hooksecurefunc(fs, "SetText", function(self, text)
		if busy[self] or not WPS.On("zone") or type(text) ~= "string" or isSecret(text) then return end
		local sv = WPS.L.zone and WPS.L.zone[text] or WPS.Name(text)
		if sv and sv ~= text then
			busy[self] = true
			self:SetText(sv)
			busy[self] = nil
		end
	end)
	WPS.hooks["Zonnamn: " .. label] = true
	-- Texten kan redan vara satt innan vi hann koppla in oss.
	local current = fs:GetText()
	if current then fs:SetText(current) end
	return true
end

---------------------------------------------------------------------------

WPS.OnLogin(function()
	HookBar(PlayerCastingBarFrame or CastingBarFrame, "spelare")
	HookBar(TargetFrameSpellBar, "mål")
	HookBar(FocusFrameSpellBar)
	HookBar(PetCastingBarFrame)

	local events = CreateFrame("Frame")
	events:RegisterEvent("PLAYER_TARGET_CHANGED")
	events:RegisterEvent("UNIT_NAME_UPDATE")
	pcall(events.RegisterEvent, events, "PLAYER_FOCUS_CHANGED")
	pcall(events.RegisterEvent, events, "NAME_PLATE_UNIT_ADDED")
	events:SetScript("OnEvent", function(_, event, unit)
		if event == "NAME_PLATE_UNIT_ADDED" then
			pcall(HookNamePlateBar, unit)
		else
			C_Timer.After(0, UpdateTargetNames)
		end
	end)

	if type(CompactUnitFrame_UpdateName) == "function" then
		hooksecurefunc("CompactUnitFrame_UpdateName", function(frame)
			if frame.unit and type(frame.unit) == "string" and frame.unit:find("^nameplate") then
				pcall(UpdateUnitName, frame)
			end
		end)
		WPS.hooks["Namnplattor (CompactUnitFrame_UpdateName)"] = true
	end
	if type(UnitFrame_Update) == "function" then
		hooksecurefunc("UnitFrame_Update", function(frame) pcall(UpdateUnitName, frame) end)
	end

	HookZoneString(ZoneTextString, "stor text")
	HookZoneString(SubZoneTextString, "underzon")
	HookZoneString(MinimapZoneText or (MinimapCluster and MinimapCluster.ZoneTextButton and MinimapCluster.ZoneTextButton.Text), "minikarta")
end)
