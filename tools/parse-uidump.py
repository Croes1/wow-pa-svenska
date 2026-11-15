# tools/parse-uidump.py — extraherar osträngade gränssnittstexter ur addonets
# SavedVariables (WPSDB.uiDump som /wps dump samlar). Nätverksfri.
#
# Bruk:
#   python3 tools/parse-uidump.py <WTF/.../wow_pa_svenska.lua> -o translation/ui/dump-YYYY-MM-DD-en.tsv
#
# Rensar bort: GameTooltip-brus (föremåls-/quest-tooltips), |T/|H/|A-markup,
# färgkodade renral, redan-svenska texter (värden ur Data/Ui.lua,
# Data/UiExtra.lua och Data/Glossary.lua) samt formatutdata som redan
# hanteras. Kontrollera gärna resultatet för hand innan översättning.
import argparse, io, re, time

def unescape(s):
    return s.replace('\\"', '"').replace("\\\\", "\\")

def read_lines(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()

def ui_paths(repo):
    return (f"{repo}/Data/Ui.lua", f"{repo}/Data/UiExtra.lua", f"{repo}/Data/Glossary.lua")

def SwedishValues(repo):
    sv_values = set()
    pair_re = re.compile(r'^\["(.*)"\]="(.*)",')
    ui_re = re.compile(r'^ui\["(.*)"\] = "(.*)"')
    for path in ui_paths(repo):
        for line in read_lines(path):
            m = pair_re.match(line.strip()) or ui_re.match(line.strip())
            if m:
                sv_values.add(unescape(m.group(2)).split('" --')[0])
    return sv_values

def extract(path, repo, manual_skips):
    sv_values = SwedishValues(repo)
    sv_contains = ("Taket ökas", "Gradpoäng", "Nästa belöningar", "Belöningar kan köpas",
                   "Säsong ", "Chance to ", "Rank #")
    lines = read_lines(path)
    start = next(i for i, l in enumerate(lines) if '"uiDump"' in l)
    rows, seen = [], set()
    for line in lines[start + 1:]:
        if line.strip() in ("},", "}"):
            break
        m = re.match(r'^\[(.*)\] = "(.*)",$', line.strip())
        if not m:
            continue
        key_raw, area = m.group(1), unescape(m.group(2))
        if len(key_raw) >= 2 and key_raw[0] == '"' and key_raw[-1] == '"':
            key = unescape(key_raw[1:-1])
        else:
            continue
        if key in seen or area == "GameTooltip":
            continue
        seen.add(key)
        if re.search(r"\|[THAH]", key):
            continue
        plain = re.sub(r"\|(?:c[0-9a-fA-F]{8}|r|cn[A-Z_]+)", "", key)
        if not re.search(r"[A-Za-z]{2}", plain):
            continue
        if re.search(r"[åäöÅÄÖ]", key):
            continue
        if key in sv_values or any(s in key for s in sv_contains) or key in manual_skips:
            continue
        rows.append((key, area))
    rows.sort()
    return rows

def main():
    ap = argparse.ArgumentParser(description="Extrahera osträngade UI-texter ur WPSDB.uiDump")
    ap.add_argument("wpsdb", help="väg till wow_pa_svenska.lua (SavedVariables)")
    ap.add_argument("-o", "--out", default=None, help="utdata-EN-TSV (standard: translation/ui/dump-<datum>-en.tsv)")
    ap.add_argument("--repo", default=None, help="reporot (standard: förälder till tools/)")
    ap.add_argument("--skip", default="", help="kommaavgränsade extra strängar att hoppa över")
    args = ap.parse_args()
    repo = args.repo
    if not repo:
        import os.path
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    today = time.strftime("%Y-%m-%d")
    out = args.out or f"{repo}/translation/ui/dump-{today}-en.tsv"
    skips = {"Maximalt", "Chaddy Stabby", "Silvergryningen"}
    if args.skip:
        for extra in args.skip.split(","):
            skips.add(extra.strip())
    rows = extract(args.wpsdb, repo, skips)
    with io.open(out, "w", encoding="utf-8") as fh:
        fh.write("id\tarea\ten\n")
        for i, (key, area) in enumerate(rows, start=1):
            text = key.replace("\t", "\\t").replace("\n", "\\n")
            fh.write("%03d\t%s\t%s\n" % (i, area, text))
    print(f"rena rader: {len(rows)} -> {out}")

if __name__ == "__main__":
    main()
