-- Dumpar allt som addonet laddar in i WPS.L till en deterministisk TSV på stdout.
--
--   lua5.1 tools/dump-runtime.lua [addon-katalog] > dump.tsv
--
-- Datafilerna laddas i samma ordning som i .toc (bara rader som börjar med Data\),
-- och varje fil anropas som WoW gör: chunk(addonnamn, WPS). Core.lua kan inte köras
-- utanför spelet; därför läses bara raden "WPS.L = { ... }" ur den och körs här, så att
-- startvärdet aldrig kan glida isär från det riktiga.
--
-- Kolumner (tabbseparerade), en rad per värde:
--   tabell  nyckeltyp  nyckel  fält  värdetyp  värde
-- nyckeltyp är "n" (tal) eller "s" (sträng): [123] och ["123"] är olika nycklar.
-- fält är "=" när posten själv är ett skalärt värde (t.ex. Npc: [3]="Köttätare"),
-- annars fältnamnet (t.ex. t, o, d i Quest). Ligger ett fält i en tabell (Quest: l={"..."})
-- skrivs det l[1], l[2], ... eller l["namn"]; djupare nästling avvisas. värdetyp är
-- "s", "n" eller "b" ("t" med tomt värde markerar en tom tabell).
-- Värdet är exakt det Lua läste in: \ \t \n \r och övriga styrtecken (samt 0x7f) skrivs
-- som \\ \t \n \r respektive \xHH, så en riktig radbrytning (\n) och de två tecknen
-- backslash+n (\\n) går att skilja åt. Bytes >= 0x80 (UTF-8) skrivs oförändrade.
-- Raderna sorteras bytevis: tabellnamn, tal före strängar, nyckel, fält.
--
-- Skriver bara till stdout. Avslutar med fel (kod 1) om något oväntat hittas, så att
-- en dump aldrig tyst utelämnar data.

os.setlocale("C") -- bytevis jämförelse av strängar, oberoende av miljön

local function fail(msg)
	io.stderr:write("dump-runtime: ", msg, "\n")
	os.exit(1)
end

local function readfile(path)
	local fh, err = io.open(path, "rb")
	if not fh then fail("kan inte läsa " .. path .. ": " .. tostring(err)) end
	local s = fh:read("*a")
	fh:close()
	return s
end

local root = arg and arg[1]
if not root then
	local script = (arg and arg[0]) or "tools/dump-runtime.lua"
	local dir = script:match("^(.*)[/\\][^/\\]*$") or "."
	root = dir .. "/.."
end
root = root:gsub("[/\\]+$", "")

-- WPS.L-startvärdet ur Core.lua
local core = readfile(root .. "/Core.lua")
local init = core:match("\nWPS%.L%s*=%s*(%b{})")
if not init then fail("hittar ingen rad 'WPS.L = { ... }' i Core.lua") end
local initFn, initErr = loadstring("return " .. init)
if not initFn then fail("kan inte tolka WPS.L-startvärdet: " .. tostring(initErr)) end
local WPS = { L = initFn() }

-- Datafiler i .toc-ordning
local files = {}
local toc = readfile(root .. "/wow_pa_svenska.toc")
for line in toc:gmatch("[^\n]+") do
	line = line:gsub("\r$", ""):gsub("^%s+", ""):gsub("%s+$", "")
	if line ~= "" and line:sub(1, 1) ~= "#" and line:match("^Data\\.+%.lua$") then
		files[#files + 1] = line:gsub("\\", "/")
	end
end
if #files == 0 then fail("inga Data\\*.lua-rader i .toc") end

for _, rel in ipairs(files) do
	local chunk, err = loadfile(root .. "/" .. rel)
	if not chunk then fail("syntaxfel i " .. rel .. ": " .. tostring(err)) end
	local ok, runErr = pcall(chunk, "wow_pa_svenska", WPS)
	if not ok then fail("fel vid körning av " .. rel .. ": " .. tostring(runErr)) end
end

for k in pairs(WPS) do
	if k ~= "L" then fail("datafilerna satte WPS." .. tostring(k) .. ", som dumpen inte täcker") end
end

local function esc(s)
	return (s:gsub("[%c\127\\]", function(c)
		if c == "\\" then return "\\\\" end
		if c == "\t" then return "\\t" end
		if c == "\n" then return "\\n" end
		if c == "\r" then return "\\r" end
		return string.format("\\x%02X", c:byte())
	end))
end

local function fmtnum(n)
	if n == math.floor(n) and math.abs(n) < 1e15 then return string.format("%d", n) end
	return string.format("%.17g", n)
end

local function value(v, where)
	local t = type(v)
	if t == "string" then return "s", esc(v) end
	if t == "number" then return "n", fmtnum(v) end
	if t == "boolean" then return "b", tostring(v) end
	fail("oväntad värdetyp " .. t .. " vid " .. where)
end

local function keyinfo(k, where)
	local t = type(k)
	if t == "number" then return "n", fmtnum(k) end
	if t == "string" then return "s", esc(k) end
	fail("oväntad nyckeltyp " .. t .. " vid " .. where)
end

-- sorteringsnyckel: tal före strängar, tal numeriskt, strängar bytevis
local function less(a, b)
	local ta, tb = type(a), type(b)
	if ta ~= tb then return ta == "number" end
	return a < b
end

local function sortedkeys(t)
	local keys = {}
	for k in pairs(t) do keys[#keys + 1] = k end
	table.sort(keys, less)
	return keys
end

local out, n = {}, 0
local function emit(...)
	n = n + 1
	out[n] = table.concat({ ... }, "\t")
end

for _, tname in ipairs(sortedkeys(WPS.L)) do
	local tbl = WPS.L[tname]
	if type(tname) ~= "string" then fail("WPS.L har icke-strängnyckel") end
	if type(tbl) ~= "table" then fail("WPS.L." .. tname .. " är inte en tabell") end
	for _, key in ipairs(sortedkeys(tbl)) do
		local where = "WPS.L." .. tname .. "[" .. tostring(key) .. "]"
		local kt, ks = keyinfo(key, where)
		local entry = tbl[key]
		if type(entry) == "table" then
			if next(entry) == nil then emit(tname, kt, ks, "{}", "t", "") end -- tom post syns ändå
			for _, field in ipairs(sortedkeys(entry)) do
				if type(field) ~= "string" then fail("fält med icke-strängnamn vid " .. where) end
				local fv = entry[field]
				if type(fv) == "table" then
					-- en nivå till (Quest: l={"spårrad", ...}); fältet skrivs l[1], l[2], ...
					if next(fv) == nil then emit(tname, kt, ks, esc(field), "t", "") end
					for _, sub in ipairs(sortedkeys(fv)) do
						local swhere = where .. "." .. field .. "[" .. tostring(sub) .. "]"
						local skt, sks = keyinfo(sub, swhere)
						local vt, vs = value(fv[sub], swhere)
						emit(tname, kt, ks, esc(field) .. (skt == "n" and "[" .. sks .. "]" or "[\"" .. sks .. "\"]"), vt, vs)
					end
				else
					local vt, vs = value(fv, where .. "." .. field)
					emit(tname, kt, ks, esc(field), vt, vs)
				end
			end
		else
			local vt, vs = value(entry, where)
			emit(tname, kt, ks, "=", vt, vs)
		end
	end
end

if n > 0 then io.stdout:write(table.concat(out, "\n"), "\n") end
