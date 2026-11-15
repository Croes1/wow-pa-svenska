-- Systemmeddelanden i chatten: byte, anseende, erfarenhet, pengar, quests, färdigheter m.m.
-- Använder ChatFrame_AddMessageEventFilter, Blizzards avsedda väg för att skriva om
-- chattrader. Ingen Blizzard-funktion ersätts och ingen secure kod körs, alltså ingen taint.
--
-- Mönstren byggs vid inloggning från klientens egna globala strängar (LOOT_ITEM_SELF osv.),
-- så de matchar exakt det klienten skriver. Saknas en sträng i klienten hoppas den över.
-- Länkar ([Föremål]) lämnas orörda: ändrad länktext gör att shift-klick och länkning
-- i chatten slutar fungera.

local _, WPS = ...

-- {n} = argument nummer n i den engelska formatsträngen.
local TEMPLATES = {
	-- Byte
	LOOT_ITEM_SELF = "Du får byte: {1}.",
	LOOT_ITEM_SELF_MULTIPLE = "Du får byte: {1}x{2}.",
	LOOT_ITEM_PUSHED_SELF = "Du får föremål: {1}.",
	LOOT_ITEM_PUSHED_SELF_MULTIPLE = "Du får föremål: {1}x{2}.",
	LOOT_ITEM_CREATED_SELF = "Du tillverkar: {1}.",
	LOOT_ITEM_CREATED_SELF_MULTIPLE = "Du tillverkar: {1}x{2}.",
	LOOT_ITEM_REFUND = "Du får tillbaka: {1}.",
	LOOT_ITEM_REFUND_MULTIPLE = "Du får tillbaka: {1}x{2}.",
	LOOT_ITEM = "{1} får byte: {2}.",
	LOOT_ITEM_MULTIPLE = "{1} får byte: {2}x{3}.",
	LOOT_ITEM_PUSHED = "{1} får föremål: {2}.",
	LOOT_ITEM_PUSHED_MULTIPLE = "{1} får föremål: {2}x{3}.",
	LOOT_ITEM_CREATED = "{1} tillverkar: {2}.",
	LOOT_ITEM_CREATED_MULTIPLE = "{1} tillverkar: {2}x{3}.",
	-- Tärningsslag om byte. I den här klienten börjar de flesta med en länk till bytesloggen
	-- (|HlootHistory:%d|h[Loot]|h: ...), där argument 1 är loggens id. Länken ska stå kvar.
	LOOT_ROLL_YOU_WON = "|HlootHistory:{1}|h[Byte]|h: Du vann: {2}",
	LOOT_ROLL_WON = "|HlootHistory:{1}|h[Byte]|h: {2} vann: {3}",
	LOOT_ROLL_ALL_PASSED = "|HlootHistory:{1}|h[Byte]|h: Alla avstod från: {2}",
	LOOT_ROLL_PASSED = "|HlootHistory:{1}|h[Byte]|h: {2} avstod från: {3}",
	LOOT_ROLL_PASSED_SELF = "|HlootHistory:{1}|h[Byte]|h: Du avstod från: {2}",
	LOOT_ROLL_PASSED_AUTO = "{1} avstod automatiskt från {2} eftersom han inte kan plundra föremålet.",
	LOOT_ROLL_PASSED_AUTO_FEMALE = "{1} avstod automatiskt från {2} eftersom hon inte kan plundra föremålet.",
	LOOT_ROLL_NEED = "|HlootHistory:{1}|h[Byte]|h: {2} har valt Behov för: {3}",
	LOOT_ROLL_NEED_SELF = "|HlootHistory:{1}|h[Byte]|h: Du har valt Behov för: {2}",
	LOOT_ROLL_GREED = "|HlootHistory:{1}|h[Byte]|h: {2} har valt Girighet för: {3}",
	LOOT_ROLL_GREED_SELF = "|HlootHistory:{1}|h[Byte]|h: Du har valt Girighet för: {2}",
	LOOT_ROLL_DISENCHANT = "{1} har valt Upplösning för: {2}",
	LOOT_ROLL_DISENCHANT_SELF = "|HlootHistory:{1}|h[Byte]|h: Du har valt Upplösning för: {2}",
	LOOT_ROLL_ROLLED_NEED = "|HlootHistory:{1}|h[Byte]|h: Behovsslag – {2} för {3} av {4}",
	LOOT_ROLL_ROLLED_GREED = "|HlootHistory:{1}|h[Byte]|h: Girighetsslag – {2} för {3} av {4}",
	LOOT_ROLL_ROLLED_DE = "Upplösningsslag – {1} för {2} av {3}",
	LOOT_ROLL_STARTED = "|HlootHistory:{1}|h[Byte]|h: {2}",
	LOOT_ITEM_BONUS_ROLL_SELF = "Du får bonusbyte: {1}",
	LOOT_DISENCHANT_CREDIT = "{1} löstes upp till byte av {2}.",
	ERR_LOOT_GONE = "Redan plundrat ({1}/{2})",
	ERR_LOOT_ROLL_PENDING = "Det slås fortfarande om föremålet.",
	RANDOM_ROLL_RESULT = "{1} slår {2} ({3}-{4})",

	-- Pengar
	YOU_LOOT_MONEY = "Du plundrar {1}",
	LOOT_MONEY = "{1} plundrar {2}.",
	LOOT_MONEY_SPLIT = "Din andel av bytet är {1}.",
	LOOT_MONEY_SPLIT_GUILD = "Din andel av bytet är {1}. ({2} skickades till gillebanken)",
	YOU_LOOT_MONEY_GUILD = "Du plundrar {1} ({2} skickades till gillebanken)",
	ERR_QUEST_REWARD_MONEY_S = "Erhöll {1}.",

	-- Anseende
	FACTION_STANDING_INCREASED = "Ditt anseende hos {1} har ökat med {2}.",
	FACTION_STANDING_DECREASED = "Ditt anseende hos {1} har minskat med {2}.",
	FACTION_STANDING_INCREASED_GENERIC = "Ditt anseende hos {1} har ökat.",
	FACTION_STANDING_DECREASED_GENERIC = "Ditt anseende hos {1} har minskat.",
	FACTION_STANDING_INCREASED_BONUS = "Ditt anseende hos {1} har ökat med {2}. (+{3} i bonus)",
	FACTION_STANDING_INCREASED_ACH_BONUS = "Ditt anseende hos {1} har ökat med {2}. (+{3} i bonus)",
	FACTION_STANDING_INCREASED_DOUBLE_BONUS = "Ditt anseende hos {1} har ökat med {2}. (+{3} i bonus, +{4} i extra bonus)",
	FACTION_STANDING_CHANGED = "Du är nu {1} hos {2}.",

	-- Erfarenhet
	COMBATLOG_XPGAIN_FIRSTPERSON = "{1} dör, du får {2} erfarenhet.",
	COMBATLOG_XPGAIN_FIRSTPERSON_UNNAMED = "Du får {1} erfarenhet.",
	COMBATLOG_XPGAIN_FIRSTPERSON_GROUP = "{1} dör, du får {2} erfarenhet. (+{3} i gruppbonus)",
	COMBATLOG_XPGAIN_FIRSTPERSON_UNNAMED_GROUP = "Du får {1} erfarenhet. (+{2} i gruppbonus)",
	COMBATLOG_XPGAIN_FIRSTPERSON_RAID = "{1} dör, du får {2} erfarenhet. (-{3} i raidavdrag)",
	COMBATLOG_XPGAIN_FIRSTPERSON_UNNAMED_RAID = "Du får {1} erfarenhet. (-{2} i raidavdrag)",
	COMBATLOG_XPGAIN_EXHAUSTION1 = "{1} dör, du får {2} erfarenhet. ({3} erf. {4}bonus)",
	COMBATLOG_XPGAIN_EXHAUSTION2 = "{1} dör, du får {2} erfarenhet. ({3} erf. {4}bonus)",
	COMBATLOG_XPGAIN_EXHAUSTION4 = "{1} dör, du får {2} erfarenhet. ({3} erf. {4}avdrag)",
	COMBATLOG_XPGAIN_EXHAUSTION5 = "{1} dör, du får {2} erfarenhet. ({3} erf. {4}avdrag)",
	COMBATLOG_XPGAIN_EXHAUSTION1_GROUP = "{1} dör, du får {2} erfarenhet. ({3} erf. {4}bonus, +{5} i gruppbonus)",
	COMBATLOG_XPGAIN_EXHAUSTION1_RAID = "{1} dör, du får {2} erfarenhet. ({3} erf. {4}bonus, -{5} i raidavdrag)",
	COMBATLOG_XPGAIN_QUEST = "Du får {1} erfarenhet. ({2} erf. {3}bonus)",
	ERR_QUEST_REWARD_EXP_I = "Erfarenhet: {1}.",
	ERR_ZONE_EXPLORED = "Upptäckt: {1}",
	ERR_ZONE_EXPLORED_XP = "Upptäckt {1}: {2} erfarenhet",
	ERR_EXHAUSTION_WELLRESTED = "Du känner dig utvilad.",
	ERR_EXHAUSTION_RESTED = "Du känner dig utvilad.",
	ERR_EXHAUSTION_NORMAL = "Du känner dig normal.",
	ERR_EXHAUSTION_TIRED = "Du känner dig trött.",
	ERR_EXHAUSTION_EXHAUSTED = "Du känner dig utmattad.",
	LEVEL_UP = "Grattis, du har nått |cffFF4E00|Hlevelup:{1}:LEVEL_UP_TYPE_CHARACTER|h[nivå {2}]|h|r!",
	LEVEL_UP_HEALTH = "Du har fått {1} hälsopoäng.",
	LEVEL_UP_HEALTH_MANA = "Du har fått {1} hälsopoäng och {2} mana.",
	LEVEL_UP_STAT = "Din {1} ökar till {2}.",
	LEVEL_UP_CHAR_POINTS = "Du har fått {1} talangpoäng.",
	LEVEL_UP_SKILL_POINTS = "Du har fått {1} färdighetspoäng.",

	-- Quests
	ERR_QUEST_ACCEPTED_S = "Uppdrag accepterat: {1}",
	ERR_QUEST_COMPLETE_S = "{1} slutfört.",
	ERR_QUEST_FAILED_S = "{1} misslyckades.",
	ERR_QUEST_ABANDONED_S = "Uppdrag övergivet: {1}",
	ERR_QUEST_REWARD_ITEM_S = "Erhöll föremål: {1}.",
	ERR_QUEST_REWARD_ITEM_MULT_IS = "Erhöll {1} av föremålet: {2}.",
	ERR_QUEST_ADD_KILL_SII = "{1} dödad: {2}/{3}",
	ERR_QUEST_ADD_FOUND_SII = "{1} hittad: {2}/{3}",
	ERR_QUEST_OBJECTIVE_COMPLETE_S = "{1} (klart)",
	ERR_QUEST_ALREADY_DONE = "Du har redan slutfört det uppdraget.",
	ERR_QUEST_LOG_FULL = "Din uppdragslogg är full.",

	-- Färdigheter och förmågor
	ERR_SKILL_GAINED_S = "Du har fått färdigheten {1}.",
	ERR_SKILL_UP_SI = "Din färdighet i {1} har ökat till {2}.",
	ERR_LEARN_SPELL_S = "Du har lärt dig en ny besvärjelse: {1}.",
	ERR_LEARN_ABILITY_S = "Du har lärt dig en ny förmåga: {1}.",
	ERR_LEARN_RECIPE_S = "Du har lärt dig att tillverka ett nytt föremål: {1}.",
	ERR_LEARN_PASSIVE_S = "Du har lärt dig en ny passiv effekt: {1}.",
	ERR_SPELL_UNLEARNED_S = "Du har glömt {1}.",
	ERR_PET_LEARN_SPELL_S = "Ditt husdjur har lärt sig en ny besvärjelse: {1}.",
	ERR_PET_LEARN_ABILITY_S = "Ditt husdjur har lärt sig en ny förmåga: {1}.",
	TRADESKILL_LOG_FIRSTPERSON = "Du tillverkar {1}.",
	TRADESKILL_LOG_THIRDPERSON = "{1} tillverkar {2}.",

	-- Resor och viloplats
	ERR_NEWTAXIPATH = "Ny flygväg upptäckt!",
	ERR_DEATHBIND_SUCCESS_S = "{1} är nu ditt hem.",
	ERR_DEATHBIND_ALREADY_BOUND = "Du är redan bunden här!",

	-- Grupp
	ERR_JOINED_GROUP_S = "{1} går med i gruppen.",
	ERR_LEFT_GROUP_S = "{1} lämnar gruppen.",
	ERR_LEFT_GROUP_YOU = "Du lämnar gruppen.",
	ERR_GROUP_DISBANDED = "Din grupp har upplösts.",
	ERR_INVITE_PLAYER_S = "Du har bjudit in {1} till din grupp.",
	ERR_DECLINE_GROUP_S = "{1} tackar nej till din gruppinbjudan.",
	ERR_NEW_LEADER_S = "{1} är nu gruppledare.",
	ERR_NEW_LEADER_YOU = "Du är nu gruppledare.",
	ERR_RAID_YOU_JOINED = "Du har gått med i en raidgrupp.",
	ERR_RAID_YOU_LEFT = "Du har lämnat raidgruppen.",
	ERR_RAID_MEMBER_ADDED_S = "{1} har gått med i raidgruppen.",
	ERR_RAID_MEMBER_REMOVED_S = "{1} har lämnat raidgruppen.",
	LOOT_METHOD_CHANGED = "Bytesfördelning ändrad till {1}.",

	-- Vänner, AFK, handel, tid
	ERR_FRIEND_ONLINE_SS = "|Hplayer:{1}|h[{2}]|h har loggat in.",
	ERR_FRIEND_OFFLINE_S = "{1} har loggat ut.",
	ERR_FRIEND_ADDED_S = "{1} har lagts till i vänlistan.",
	ERR_FRIEND_REMOVED_S = "{1} har tagits bort från vänlistan.",
	MARKED_AFK = "Du är nu borta.",
	MARKED_AFK_MESSAGE = "Du är nu borta: {1}",
	CLEARED_AFK = "Du är inte längre borta.",
	MARKED_DND = "Du är nu upptagen: {1}.",
	CLEARED_DND = "Du är inte längre upptagen.",
	ERR_TRADE_COMPLETE = "Handeln genomförd.",
	ERR_TRADE_CANCELLED = "Handeln avbröts.",
	TIME_PLAYED_TOTAL = "Total speltid: {1}",
	TIME_PLAYED_LEVEL = "Speltid på denna nivå: {1}",
	ERR_DUEL_REQUESTED = "Du har utmanat till duell.",
	DUEL_WINNER_KNOCKOUT = "{1} har besegrat {2} i en duell",
	DUEL_WINNER_RETREAT = "{2} har flytt från en duell med {1}",
	ERR_DUEL_CANCELLED = "Duellen avbröts.",

	-- Samlingar
	ERR_LEARN_TRANSMOG_S = "{1} har lagts till i din utseendesamling.",
	ERR_REVOKE_TRANSMOG_S = "{1} har tagits bort från din utseendesamling.",
	ERR_LEARN_COMPANION_S = "Du har lagt till husdjuret {1} i din samling.",
	ERR_LEARN_MOUNT_S = "Du har lagt till riddjuret {1} i din samling.",
	ERR_LEARN_TOY_S = "{1} har lagts till i din leksakslåda.",
	ERR_LEARN_HEIRLOOM_S = "{1} har lagts till i din arvegodssamling.",
	ERR_PET_SPELL_UNLEARNED_S = "Ditt husdjur har glömt {1}.",

	-- Grupp och raid
	ERR_INVITED_TO_GROUP_SS = "|Hplayer:{1}|h[{2}]|h har bjudit in dig till en grupp.",
	ERR_NEW_LOOT_MASTER_S = "{1} är nu bytesmästare.",
	ERR_SET_LOOT_GROUP = "Bytesfördelningen är nu Gruppbyte.",
	ERR_SET_LOOT_FREEFORALL = "Bytesfördelningen är nu Fritt för alla.",
	ERR_SET_LOOT_ROUNDROBIN = "Bytesfördelningen är nu Turordning.",
	ERR_SET_LOOT_NBG = "Bytesfördelningen är nu Behov före girighet.",
	ERR_SET_LOOT_THRESHOLD_S = "Bytesgränsen är nu {1}.",
	ERR_PARTY_CONVERTED_TO_RAID = "Gruppen har gjorts om till en raid",
	ERR_NOT_IN_GROUP = "Du är inte med i en grupp.",
	ERR_NOT_IN_RAID = "Du är inte med i en raidgrupp",
	ERR_PLAYER_DIED_S = "{1} har dött.",
	INSTANCE_RESET_SUCCESS = "{1} har återställts.",
	INSTANCE_RESET_FAILED = "Det går inte att återställa {1}. Det finns fortfarande spelare i instansen.",
	ERR_DUNGEON_DIFFICULTY_CHANGED_S = "Svårighetsgraden för instanser är nu {1}.",
	ERR_RAID_DIFFICULTY_CHANGED_S = "Svårighetsgraden för raider är nu {1}.",
	ERR_LFG_JOINED_QUEUE = "Du står nu i kö i instanssökaren.",
	ERR_LFG_LEFT_QUEUE = "Du står inte längre i kö.",

	-- Uppdrag som delas och räknas
	ERR_QUEST_PUSH_SUCCESS_S = "Delar uppdraget med {1} ...",
	ERR_QUEST_PUSH_ACCEPTED_S = "{1} har accepterat ditt uppdrag.",
	ERR_QUEST_PUSH_DECLINED_S = "{1} har tackat nej till ditt uppdrag.",
	ERR_QUEST_PUSH_ALREADY_DONE_S = "{1} har redan slutfört det uppdraget.",
	ERR_QUEST_PUSH_LOG_FULL_S = "Uppdragsloggen för {1} är full.",
	ERR_QUEST_PUSH_ONQUEST_S = "{1} har redan det uppdraget.",
	ERR_QUEST_PUSH_ONQUEST_TO_RECIPIENT_S = "{1} försökte dela uppdraget \"{2}\", men du har redan det uppdraget.",
	ERR_QUEST_UNKNOWN_COMPLETE = "Målet uppfyllt.",
	ERR_QUEST_ADD_ITEM_SII = "{1}: {2}/{3}",
	ERR_QUEST_ADD_PLAYER_KILL_SII = "Dödade spelare: {1}/{2}",

	-- Auktionshuset
	ERR_AUCTION_STARTED = "Auktionen har skapats.",
	ERR_AUCTION_SOLD_S = "En köpare har hittats för din auktion av {1}.",
	ERR_AUCTION_WON_S = "Du vann en auktion på {1}",
	ERR_AUCTION_OUTBID_S = "Någon har bjudit över dig på {1}.",
	ERR_AUCTION_EXPIRED_S = "Din auktion av {1} har gått ut.",
	ERR_AUCTION_REMOVED_S = "Din auktion av {1} har avbrutits av säljaren.",

	-- Gille, vänner, ignorera
	ERR_GUILD_JOIN_S = "{1} har gått med i gillet.",
	ERR_GUILD_LEAVE_S = "{1} har lämnat gillet.",
	ERR_GUILD_INVITE_S = "Du har bjudit in {1} till ditt gille.",
	ERR_GUILD_PROMOTE_SSS = "{1} har befordrat {2} till {3}.",
	ERR_GUILD_DEMOTE_SSS = "{1} har degraderat {2} till {3}.",
	ERR_GUILD_REMOVE_SS = "{1} har sparkats ut ur gillet av {2}.",
	ERR_FRIEND_NOT_FOUND = "Spelaren hittades inte.",
	ERR_FRIEND_ALREADY_S = "{1} är redan din vän.",
	ERR_IGNORE_ADDED_S = "{1} ignoreras nu.",
	ERR_IGNORE_REMOVED_S = "{1} ignoreras inte längre.",
	ERR_CHAT_PLAYER_NOT_FOUND_S = "Ingen spelare som heter '{1}' spelar just nu.",
	ERR_CHAT_THROTTLED = "Antalet meddelanden du kan skicka är begränsat. Vänta innan du skickar nästa.",
	ERR_TOO_MANY_CHAT_CHANNELS = "Du kan bara vara med i {1} kanaler åt gången.",

	-- Handel, fiske, flyg, övrigt
	ERR_TRADE_REQUEST_S = "{1} vill handla med dig.",
	ERR_TRADE_BLOCKED_S = "{1} ville handla. Du har tackat nej.",
	ERR_FISH_ESCAPED = "Fisken kom undan!",
	ERR_FISH_NOT_HOOKED = "Ingen fisk har nappat.",
	ERR_TAXINOVENDORNEARBY = "Det finns ingen flygmästare i närheten!",
	ERR_TAXINOPATHS = "Du känner inte till några platser som har förbindelse med den här.",
	ERR_RECEIVE_ITEM_S = "{1} mottaget.",
	ERR_UNKNOWN_MACRO_OPTION_S = "Okänt makroval: {1}",
}

-- Ord inuti argumenten (anseendenivåer, vila, pengar, tid).
local WORDS = {
	Hated = "hatad", Hostile = "fientlig", Unfriendly = "ovänlig", Neutral = "neutral",
	Friendly = "vänlig", Honored = "ärad", Revered = "vördad", Exalted = "upphöjd",
	Rested = "vilo", ["Group Raid Penalty"] = "raid",
	Strength = "styrka", Agility = "smidighet", Stamina = "uthållighet",
	Intellect = "intellekt", Spirit = "ande",
	["Need before Greed"] = "Behov före girighet", ["Group Loot"] = "Gruppbyte",
	-- Färdigheter
	Swords = "svärd", ["Two-Handed Swords"] = "tvåhandssvärd", Axes = "yxor", ["Two-Handed Axes"] = "tvåhandsyxor",
	Maces = "klubbor", ["Two-Handed Maces"] = "tvåhandsklubbor", Daggers = "dolkar", Staves = "stavar",
	Polearms = "stångvapen", Bows = "bågar", Guns = "gevär", Crossbows = "armborst", Thrown = "kastvapen",
	Wands = "trollstavar", Unarmed = "obeväpnad", ["Fist Weapons"] = "knytnävsvapen", Defense = "försvar",
	["First Aid"] = "första hjälpen", Cooking = "matlagning", Fishing = "fiske", Mining = "gruvbrytning",
	Herbalism = "örtkunskap", Skinning = "flåning", Blacksmithing = "smide", Leatherworking = "lädersmide",
	Tailoring = "skrädderi", Engineering = "ingenjörskonst", Alchemy = "alkemi", Enchanting = "förtrollning",
	Lockpicking = "dyrkning", Riding = "ridning",
	Poor = "Dålig", Common = "Vanlig", Uncommon = "Ovanlig", Rare = "Sällsynt", Epic = "Episk",
	["Free for All"] = "Fritt för alla", ["Round Robin"] = "Turordning", ["Master Looter"] = "Bytesmästare",
}
local MONEY = { Gold = "guld", Silver = "silver", Copper = "koppar" }
local TIME = { days = "dagar", day = "dag", hours = "timmar", hour = "timme",
	minutes = "minuter", minute = "minut", seconds = "sekunder", second = "sekund" }

-- Uppdragstitlar i meddelanden ("Quest accepted: X"): leta upp questen i loggen.
local QUEST_ARGS = {
	ERR_QUEST_ACCEPTED_S = 1, ERR_QUEST_COMPLETE_S = 1, ERR_QUEST_FAILED_S = 1,
	ERR_QUEST_ABANDONED_S = 1, ERR_QUEST_PUSH_ONQUEST_TO_RECIPIENT_S = 2,
}
local questTitles = {} -- engelsk titel -> quest-ID, fylls på när loggen läses

local function RememberQuestLog()
	if not (C_QuestLog and C_QuestLog.GetNumQuestLogEntries and C_QuestLog.GetInfo) then return end
	for i = 1, C_QuestLog.GetNumQuestLogEntries() do
		local info = C_QuestLog.GetInfo(i)
		if info and info.questID and info.title and not info.isHeader then
			questTitles[info.title] = info.questID
		end
	end
end

local function QuestTitle(title)
	if not questTitles[title] then RememberQuestLog() end
	local q = WPS.L.quest[questTitles[title]]
	return q and q.t or title
end

local function Word(s)
	if s:find("|H", 1, true) then return s end -- länk: rör inte
	local direct = WPS.Name(s) or WORDS[s]
	if direct then return direct end
	s = s:gsub("(%d+) (%a+)", function(n, unit)
		local sv = MONEY[unit] or TIME[unit:lower()]
		if sv then return n .. " " .. sv end
	end)
	return s
end

---------------------------------------------------------------------------
-- Formatsträng -> Lua-mönster
---------------------------------------------------------------------------

local function Escape(s)
	return (s:gsub("[%^%$%(%)%%%.%[%]%*%+%-%?]", "%%%0"))
end

-- Returnerar mönster, argumentnummer per fångst, antal bokstavliga tecken (för sortering).
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
			pat[#pat + 1] = "%%"
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

-- UI.lua använder samma kompilator för gränssnittets formatsträngar ("Sida %d/%d").
WPS.CompileFormat = Compile

local rules = {}

local function BuildRules()
	for key, sv in pairs(TEMPLATES) do
		local fmt = _G[key]
		if type(fmt) == "string" and fmt ~= "" then
			local pat, order, literal = Compile(fmt)
			rules[#rules + 1] = { key = key, pat = pat, order = order, literal = literal, sv = sv }
		end
	end
	-- Mest specifika mönstret först, så att t.ex. "%s: %d/%d" inte äter allt.
	table.sort(rules, function(a, b) return a.literal > b.literal end)
end

local function Translate(msg)
	for _, r in ipairs(rules) do
		local caps = { msg:match(r.pat) }
		if caps[1] ~= nil then
			local args = {}
			for i, n in ipairs(r.order) do
				local v = caps[i]
				if QUEST_ARGS[r.key] == n then v = QuestTitle(v) else v = Word(v) end
				args[n] = v
			end
			return (r.sv:gsub("{(%d)}", function(n) return args[tonumber(n)] or "" end))
		end
	end
end

---------------------------------------------------------------------------
-- Filter
---------------------------------------------------------------------------

local isSecret = issecretvalue or function() return false end

-- Samma meddelande filtreras en gång per chattfönster; spara senaste resultatet.
local lastIn, lastOut

local function SystemFilter(_, _, msg, ...)
	if not WPS.On("chat") or type(msg) ~= "string" or isSecret(msg) then return false, msg, ... end
	if msg ~= lastIn then
		local ok, out = pcall(Translate, msg)
		lastIn, lastOut = msg, ok and out or nil
		pcall(function() -- för /wps fel; får aldrig störa chatten
			local recent = WPS.last.chat and WPS.last.chat.lines or {}
			table.insert(recent, 1, { en = msg, sv = lastOut })
			recent[6] = nil
			WPS.Remember("chat", { lines = recent })
		end)
	end
	if lastOut then return false, lastOut, ... end
	return false, msg, ...
end

-- Vanliga varelse-emotes. Klienten sätter in namnet i %s när raden visas.
local EMOTES = {
	["%s attempts to run away in fear!"] = "%s försöker fly i skräck!",
	["%s goes into a frenzy!"] = "%s blir vansinnig av raseri!",
	["%s becomes enraged!"] = "%s blir rasande!",
	["%s goes into a berserker rage!"] = "%s går in i bärsärkaraseri!",
	["%s calls for help!"] = "%s ropar på hjälp!",
	["%s flees in terror!"] = "%s flyr i panik!",
}

-- NPC-repliker: byt talarens namn mot det svenska via NPC-ID:t i GUID:en (arg 12).
local function NpcFilter(_, _, msg, author, ...)
	if not WPS.On("npc") then return false, msg, author, ... end
	if type(msg) == "string" and not isSecret(msg) and EMOTES[msg] then msg = EMOTES[msg] end
	local guid = select(10, ...)
	local ok, name = pcall(function()
		if isSecret(guid) or type(guid) ~= "string" then return end
		local unitType, id = guid:match("^(%a+)%-%d+%-%d+%-%d+%-%d+%-(%d+)")
		if unitType == "Creature" or unitType == "Vehicle" then
			return WPS.L.npc[tonumber(id)]
		end
	end)
	if ok and name then return false, msg, name, ... end
	return false, msg, author, ...
end

local SYSTEM_EVENTS = {
	"CHAT_MSG_SYSTEM", "CHAT_MSG_LOOT", "CHAT_MSG_MONEY", "CHAT_MSG_COMBAT_FACTION_CHANGE",
	"CHAT_MSG_COMBAT_XP_GAIN", "CHAT_MSG_SKILL", "CHAT_MSG_TRADESKILLS", "CHAT_MSG_OPENING",
	"CHAT_MSG_COMBAT_MISC_INFO", "CHAT_MSG_COMBAT_HONOR_GAIN",
}
local NPC_EVENTS = {
	"CHAT_MSG_MONSTER_SAY", "CHAT_MSG_MONSTER_YELL", "CHAT_MSG_MONSTER_EMOTE",
	"CHAT_MSG_MONSTER_WHISPER", "CHAT_MSG_MONSTER_PARTY", "CHAT_MSG_RAID_BOSS_EMOTE",
	"CHAT_MSG_RAID_BOSS_WHISPER",
}

WPS.Chat = { Translate = function(msg) return Translate(msg) end }

WPS.OnLogin(function()
	local ok = type(ChatFrame_AddMessageEventFilter) == "function"
	WPS.hooks["ChatFrame_AddMessageEventFilter"] = ok
	if not ok then return end
	BuildRules()
	for _, e in ipairs(SYSTEM_EVENTS) do ChatFrame_AddMessageEventFilter(e, SystemFilter) end
	for _, e in ipairs(NPC_EVENTS) do ChatFrame_AddMessageEventFilter(e, NpcFilter) end

	local f = CreateFrame("Frame")
	f:RegisterEvent("QUEST_LOG_UPDATE")
	f:SetScript("OnEvent", RememberQuestLog)
end)
