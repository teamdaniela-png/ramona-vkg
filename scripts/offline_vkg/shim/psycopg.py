"""sqlite-backed stand-in for psycopg, so scripts/ingest_ctdc.py and scripts/ingest_unodc.py run unchanged offline."""
import os, re, sqlite3
class _Cur:
    def __init__(s, c): s.c=c.cursor()
    def __enter__(s): return s
    def __exit__(s,*a): pass
    def _t(s, q): return re.sub(r"\b(ramona|public)\.","",q.replace("%s","?"))
    def execute(s,q,p=()): s.c.execute(s._t(q),p)
    def executemany(s,q,ps): s.c.executemany(s._t(q),ps)
    def fetchone(s): return s.c.fetchone()
class _Conn:
    def __init__(s,path): s.k=sqlite3.connect(path); s.k.execute("PRAGMA foreign_keys=ON")
    def __enter__(s): return s
    def __exit__(s,*a): s.k.commit(); s.k.close()
    def cursor(s): return _Cur(s.k)
    def commit(s): s.k.commit()
def connect(dsn): return _Conn(os.environ["SQLITE_PATH"])
