-- tools/check-ui-translation.lua — offline-kontroll av ett UI-översättningspar:
--   lua5.1 tools/check-ui-translation.lua translation/ui/dump-<datum>-en.tsv translation/ui/dump-<datum>-sv.tsv
--
-- Laddar riktiga tabeller (Data/Ui.lua + Data/UiExtra.lua), bygger exakt- och
-- formatmatchning som UI.lua gör (Compile/Fill ur Chat.lua) och jämför varje
-- en-rads svar mot sv-filen. Rader där översättningen är oförändrad godtas
-- (brus). Exit 0 = OK, 1 = FEL. Kör från reporoten. Nätverksfri.
local function Escape(s)
	return (s:gsub("[%^%$%(%)%%%.%[%]%*%+%-%?]", "%%%0"))
end

local function Compile(fmt)
	local pat, order, literal, pos, seq = { "^" }, {}, 0, 1, 0
	while true do
		local s, e, num, dollar, conv = fmt:find("%%(%d*)(%$?)[%-%.%d]*([sdfi%%])", pos)
		local text = fmt:sub(pos, (s or 0) - 1)
		if not s then text = fmt:sub(pos) end
		pat[#pat + 1] = Escape(text)
		literal = literal + #text
		if not s then break end
		if conv == "%" then
			pat[#pat + 1] = "%"
			literal = literal + 1
		else
			seq = seq + 1
			order[#order + 1] = (dollar == "$" and tonumber(num)) or seq
			pat[#pat + 1] = conv == "s" and "(.-)" or "([%d%.,%-]+)"
		end
		pos = e + 1
	end
	pat[#pat + 1] = "$"
	return table.concat(pat), order, literal
end

local function Fill(fmt, args)
	local seq = 0
	return (fmt:gsub("%%(%d*)(%$?)[%-%.%d]*([sdfi%%])", function(num, dollar, conv)
		if conv == "%" then return "%" end
		seq = seq + 1
		return args[(dollar == "$" and tonumber(num)) or seq] or ""
	end))
end

local function Unesc(s)
	return (s:gsub("\\n", "\n"):gsub("\\t", "\t"))
end

local function ReadRows(path)
	local rows = {}
	for line in io.lines(path) do
		-- format id[\tarea]\ttext; fält med tabbar är escape:ade (\t)
		local fields = {}
		for f in (line .. "\t"):gmatch("(.-)\t") do
			fields[#fields + 1] = f
		end
		local id = fields[1]
		if id and id ~= "id" and fields[3] then
			rows[#rows + 1] = { id = id, area = fields[2], text = Unesc(fields[3]) }
		elseif id and id ~= "id" and fields[2] then
			rows[#rows + 1] = { id = id, area = "sv", text = Unesc(fields[2]) }
		end
	end
	return rows
end

local wps = { L = {} }
assert(loadfile("Data/Ui.lua"))(nil, wps)
assert(loadfile("Data/UiExtra.lua"))(nil, wps)
local ui = wps.L.ui

local formats = {}
for en, sv in pairs(ui) do
	if en:find("%%[%d%$%.%-]*[sdfi]") then
		local pat, order, literal = Compile(en)
		formats[#formats + 1] = { pat = pat, order = order, sv = sv, literal = literal }
	end
end
table.sort(formats, function(a, b) return a.literal > b.literal end)

local function Translate(text)
	local sv = ui[text]
	if sv then return sv end
	for _, f in ipairs(formats) do
		local caps = { text:match(f.pat) }
		if caps[1] ~= nil then
			local args = {}
			for i, nn in ipairs(f.order) do args[nn] = caps[i] end
			return Fill(f.sv, args)
		end
	end
	return nil
end

local en = ReadRows(arg[1] or error("användning: check-ui-translation.lua <en.tsv> <sv.tsv>"))
local sv = ReadRows(arg[2] or error("användning: check-ui-translation.lua <en.tsv> <sv.tsv>"))
local byId = {}
for _, r in ipairs(sv) do
	if byId[r.id] then error("dubbelt id i sv-filen: " .. r.id) end
	byId[r.id] = r.text
end

local ok, err = 0, 0
for _, r in ipairs(en) do
	local want = byId[r.id]
	if want == nil then
		print(("FEL: %s saknas i sv-filen (%s)"):format(r.id, r.text))
		err = err + 1
	elseif want == r.text then
		ok = ok + 1 -- medveten oförändrad rad (brus/identisk)
	elseif Translate(r.text) == want then
		ok = ok + 1
	else
		print(("FEL: %s: översättningen matchar ej. en=%q väntat=%q got=%q")
			:format(r.id, r.text, want, Translate(r.text) or "()"))
		err = err + 1
	end
end
print(("rader: %d (ok: %d, oförändrade: %d, fel: %d)")
	:format(#en, #en - err, ok - (#en - err), err))
print(err == 0 and "RESULTAT: OK" or "RESULTAT: FEL")
os.exit(err == 0 and 0 or 1)