-- Exporterar ordlistan i Data/Glossary.lua till TSV (tabb-separerad): tabell, engelska, svenska.
-- Skriver bara till stdout; omdirigera till en fil utanför repot, t.ex. i arbetskatalogen:
--   lua5.1 tools/export-glossary.lua core  >  <arbetskatalog>/glossary-core.tsv   (den kurerade ordlistan)
--   lua5.1 tools/export-glossary.lua all   >  <arbetskatalog>/glossary-all.tsv    (även spell-/item-namn och questrader)
-- Läser alltid Data/Glossary.lua i det här repot, oavsett varifrån verktyget körs.
local scriptDir = (arg and arg[0] or ""):match("^(.*[/\\])") or "./"
local base = scriptDir .. "../Data/"
local mode = (arg and arg[1]) or "core"

-- Den kurerade ordlistan: orter, varelser och föremål ur uppdragen + fraktioner, raser, klasser.
local CORE = { "names_glossary_zone", "names_glossary_npc", "names_glossary_item", "names_general" }
local ALL = {
	"names_glossary_zone", "names_glossary_npc", "names_glossary_item", "names_general",
	"names_npc", "names_zone", "names_spell", "names_item", "qtext",
}

local WPS = { L = {} }
local chunk = assert(loadfile(base .. "Glossary.lua"))
setfenv(chunk, setmetatable({}, { __index = _G })) -- Lua 5.1, som i WoW
chunk(nil, WPS)

-- Kontrolltecken (tabbar, radbrytningar) kodas, så TSV-raden förblir en rad.
local function esc(s)
	if type(s) ~= "string" then s = tostring(s) end
	return (s:gsub("\\", "\\\\"):gsub("%c", function(c) return ("\\x%02x"):format(c:byte()) end))
end

local wanted = mode == "all" and ALL or CORE
print("table\tenglish\tswedish")
for _, name in ipairs(wanted) do
	local t = WPS.L[name]
	if type(t) ~= "table" then
		io.stderr:write("SAKNAS: " .. name .. "\n")
	else
		local keys = {}
		for k in pairs(t) do keys[#keys + 1] = k end
		table.sort(keys)
		for _, k in ipairs(keys) do
			print(("%s\t%s\t%s"):format(name, esc(k), esc(t[k])))
		end
	end
end