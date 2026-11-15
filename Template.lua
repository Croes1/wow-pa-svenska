-- Spellbeskrivningar innehåller variabler ($s1, $d, ${$s1*2} ...) som spelet själv räknar ut
-- för den engelska texten. För att få samma värden i den svenska mallen jämför vi den
-- engelska mallen med spelets färdiga engelska text och plockar ut vad varje variabel blev.
-- Går något inte att tolka (t.ex. villkor $?...) returneras nil och engelskan visas.

local _, WPS = ...

local function Tokenize(s)
	local out, lit, i, n = {}, {}, 1, #s
	local function flush()
		if #lit > 0 then
			out[#out + 1] = { kind = "lit", text = table.concat(lit) }
			lit = {}
		end
	end
	while i <= n do
		local c = s:sub(i, i)
		if c ~= "$" then
			lit[#lit + 1] = c
			i = i + 1
		else
			local nx = s:sub(i + 1, i + 1)
			local tok, kind, j
			if nx == "{" then
				local depth, k = 0, i + 1
				while k <= n do
					local ch = s:sub(k, k)
					if ch == "{" then
						depth = depth + 1
					elseif ch == "}" then
						depth = depth - 1
						if depth == 0 then break end
					end
					k = k + 1
				end
				if k > n then return nil end
				tok, kind, j = s:sub(i, k), "val", k + 1
			elseif nx == "/" then
				-- Division: $/5;s1 eller $/87;20187s3
				local m = s:match("^%$/%d+;%$?%d*%a+%d*", i)
				if not m then return nil end
				tok, kind, j = m, "val", i + #m
			elseif nx == "<" then
				local k = s:find(">", i, true)
				if not k then return nil end
				tok, kind, j = s:sub(i, k), "val", k + 1
			elseif nx == "l" or nx == "L" then
				local k = s:find(";", i, true)
				if not k then return nil end
				tok, kind, j = s:sub(i, k), "plural", k + 1
			elseif nx == "?" or nx == "g" or nx == "G" then
				return nil
			else
				local m = s:match("^%$@?%d*%a+%d*", i)
				if not m then
					lit[#lit + 1] = c
					i = i + 1
				else
					tok, kind, j = m, "val", i + #m
				end
			end
			if tok then
				flush()
				out[#out + 1] = { kind = kind, text = tok }
				i = j
			end
		end
	end
	flush()
	return out
end

local function Escape(s)
	return (s:gsub("[%^%$%(%)%%%.%[%]%*%+%-%?]", "%%%0"))
end

-- Spelets färdiga värden är på engelska: "30 sec", "1.5 min", "36 to 47". Enheterna och
-- decimaltecknet görs svenska innan värdet sätts in i den svenska mallen.
local UNITS = {
	sec = "sek", secs = "sek", second = "sekund", seconds = "sekunder",
	min = "min", mins = "min", minute = "minut", minutes = "minuter",
	hr = "tim", hrs = "tim", hour = "timme", hours = "timmar",
	day = "dag", days = "dagar", yd = "m", yds = "m", yard = "meter", yards = "meter",
}

local function LocalizeValue(v)
	v = v:gsub("(%d) to (%d)", "%1 till %2")
	v = v:gsub("(%d)%.(%d)", "%1,%2")
	v = v:gsub("(%d) (%a+)", function(d, w)
		local sv = UNITS[w:lower()]
		return sv and (d .. " " .. sv) or nil
	end)
	return v
end
WPS.LocalizeValue = LocalizeValue

local function ResolvePlain(engTpl, svTpl, resolved)
	if not svTpl then return nil end
	if not svTpl:find("$", 1, true) then return svTpl end
	if not engTpl or not resolved then return nil end

	local eng, sv = Tokenize(engTpl), Tokenize(svTpl)
	if not eng or not sv then return nil end

	local parts, tokens = { "^" }, {}
	for _, t in ipairs(eng) do
		if t.kind == "lit" then
			parts[#parts + 1] = Escape(t.text)
		elseif t.kind == "plural" then
			parts[#parts + 1] = "(%a+)"
			tokens[#tokens + 1] = false
		else
			parts[#parts + 1] = "(.-)"
			tokens[#tokens + 1] = t.text
		end
	end
	parts[#parts + 1] = "$"

	local caps = { resolved:match(table.concat(parts)) }
	if #caps ~= #tokens then return nil end
	local values = {}
	for idx, tok in ipairs(tokens) do
		if tok and values[tok] == nil then values[tok] = LocalizeValue(caps[idx]) end
	end

	local out = {}
	for _, t in ipairs(sv) do
		if t.kind == "lit" then
			out[#out + 1] = t.text
		elseif t.kind == "plural" then
			local one, many = t.text:match("^%$[lL]([^:]*):([^;]*);$")
			if not one then return nil end
			local num = table.concat(out):match("([%d%.,]+)%s*$")
			out[#out + 1] = (num == "1") and one or many
		else
			local v = values[t.text]
			if v == nil then return nil end
			out[#out + 1] = v
		end
	end
	return table.concat(out)
end

---------------------------------------------------------------------------
-- Villkor: $?a123[text om sant][text om falskt], även kedjor $?a1[A]?a2[B][C].
-- Spelet har redan valt gren i den färdiga texten. Vi provar varje kombination av
-- grenar i den engelska mallen och använder samma val i den svenska.
---------------------------------------------------------------------------

-- Delar upp en mall i { "text", {gren1, gren2, ...}, "text", ... }. nil om den inte går att tolka.
local function SplitConditions(s)
	local out, pos = {}, 1
	while true do
		local q = s:find("$?", pos, true)
		if not q then
			out[#out + 1] = s:sub(pos)
			return out
		end
		out[#out + 1] = s:sub(pos, q - 1)
		local branches, i = {}, q + 2
		while true do
			local open = s:find("[", i, true)
			if not open then return nil end
			local close = s:find("]", open, true)
			if not close or s:sub(open + 1, close - 1):find("[", 1, true) then return nil end
			branches[#branches + 1] = s:sub(open + 1, close - 1)
			i = close + 1
			local nx = s:sub(i, i)
			if nx == "?" then
				i = i + 1 -- nästa villkor i kedjan
			elseif nx ~= "[" then
				break -- sista grenen saknar else-del
			end
		end
		out[#out + 1] = branches
		pos = i
	end
end

local function Pick(parts, choice)
	local out, c = {}, 0
	for _, p in ipairs(parts) do
		if type(p) == "string" then
			out[#out + 1] = p
		else
			c = c + 1
			out[#out + 1] = p[choice[c]] or ""
		end
	end
	return (table.concat(out):gsub("%s+$", ""))
end

-- engTpl: engelsk mall, svTpl: svensk mall, resolved: spelets färdiga engelska text.
function WPS.Resolve(engTpl, svTpl, resolved)
	if not (engTpl and svTpl and engTpl:find("$?", 1, true)) then
		return ResolvePlain(engTpl, svTpl, resolved)
	end
	local eng, sv = SplitConditions(engTpl), SplitConditions(svTpl)
	if not eng or not sv or #eng ~= #sv then return nil end
	local sizes = {}
	for idx, p in ipairs(eng) do
		if type(p) == "table" then
			if type(sv[idx]) ~= "table" or #sv[idx] ~= #p then return nil end
			sizes[#sizes + 1] = #p + 1 -- +1: ingen gren (tomt)
		end
	end
	if #sizes > 3 then return nil end
	resolved = resolved and resolved:gsub("%s+$", "")
	local choice = {}
	local function Try(k)
		if k > #sizes then
			return ResolvePlain(Pick(eng, choice), Pick(sv, choice), resolved)
		end
		for b = 1, sizes[k] do
			choice[k] = b
			local r = Try(k + 1)
			if r then return r end
		end
	end
	return Try(1)
end
