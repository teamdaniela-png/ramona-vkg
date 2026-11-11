"""Load the Postgres seed files into SQLite so the mappings can be exercised offline.
Only dialect translation is applied; no datum is altered.

Usage: load_sqlite.py <repository root> <output.db>
"""
import io, os, re, sqlite3, sys, glob

REPO, DB = sys.argv[1], sys.argv[2]
if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=OFF")

def strip_comments(sql):
    out, inq = [], False
    for line in sql.split("\n"):
        res, i = [], 0
        while i < len(line):
            c = line[i]
            if c == "'":
                inq = not inq; res.append(c); i += 1; continue
            if not inq and line.startswith("--", i):
                break
            res.append(c); i += 1
        out.append("".join(res))
    return "\n".join(out)

def translate(sql):
    sql = strip_comments(sql)
    sql = re.sub(r"CREATE SCHEMA[^;]*;", "", sql, flags=re.I)
    sql = re.sub(r"\bSET\s+search_path[^;]*;", "", sql, flags=re.I)
    sql = re.sub(r"\b(ramona|public)\.", "", sql, flags=re.I)
    sql = re.sub(r"\b(BIG)?SERIAL\b", "INTEGER", sql, flags=re.I)
    sql = re.sub(r"\bTIMESTAMPTZ\b", "TEXT", sql, flags=re.I)
    sql = re.sub(r"\bNOW\(\)", "CURRENT_TIMESTAMP", sql, flags=re.I)
    sql = re.sub(r"ADD COLUMN IF NOT EXISTS", "ADD COLUMN", sql, flags=re.I)
    sql = re.sub(r"\b(DATE|TIMESTAMP|TIMESTAMPTZ|TIME)\s+(')", r"\2", sql, flags=re.I)
    return sql

def split_stmts(sql):
    stmts, buf, inq = [], [], False
    for ch in sql:
        buf.append(ch)
        if ch == "'": inq = not inq
        elif ch == ";" and not inq:
            stmts.append("".join(buf)); buf = []
    if "".join(buf).strip(): stmts.append("".join(buf))
    return stmts

SKIP = re.compile(r"^\s*(BEGIN|COMMIT|COMMENT\s+ON|SELECT\s+setval|CREATE\s+(OR\s+REPLACE\s+)?(VIEW|FUNCTION|INDEX))\b", re.I)
constraints, errors = [], []
for f in sorted(glob.glob(os.path.join(REPO, "db", "*.sql"))):
    base = os.path.basename(f)
    ok = err = 0
    for st in split_stmts(translate(io.open(f, encoding="utf-8").read())):
        s = st.strip()
        if not s or s == ";" or SKIP.match(s): continue
        if re.search(r"ALTER\s+TABLE.*ADD\s+CONSTRAINT", s, re.I | re.S):
            constraints.append((base, " ".join(s.split()))); continue
        try:
            con.execute(s); ok += 1
        except Exception as e:
            if "duplicate column name" in str(e): continue
            err += 1; errors.append((base, str(e)[:130], " ".join(s.split())[:160]))
    con.commit()
    print("%-34s ok=%-5d err=%d" % (base, ok, err))

if errors:
    print("\n--- %d statement errors ---" % len(errors))
    for b, e, s in errors[:25]: print("  [%s] %s\n      %s" % (b, e, s))
print("\n--- constraints SQLite cannot add after the fact (verified separately) ---")
for n, s in constraints: print("  ", n, "::", s[:150])
print("\n--- row counts ---")
for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print("  %-34s %d" % (t, con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]))
con.close()
