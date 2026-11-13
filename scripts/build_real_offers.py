#!/usr/bin/env python3
"""
Step 3 of the press-offer corpus: merges data/processed/offers/extracted_*.jsonl (the reading of
the press passages), repairs broken accents, removes legitimate job calls without victims, adds
the country of the article and removes duplicates (the same case reported by several outlets).

Outputs (metadata, own paraphrases and short quotes of the advertisement with their source):
  data/real/press_offers.csv
  data/real/press_offer_sources.csv  (one row per article that documents each offer)
  data/real/press_offers_stats.json
"""
import csv
import glob
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/processed/offers"
OUT = ROOT / "data/real"

FIELDS = ["offer_uid", "n_sources", "countries", "job_title", "pay_amount", "pay_currency", "pay_period", "platform",
          "offer_location", "victim_origin", "target_profile", "requirements", "contact_method", "verbatim_quote",
          "paraphrase", "type_a_flags", "type_b_flags", "criminal_recruitment", "scheme", "outcome", "event_year",
          "confidence", "outlets", "urls", "published_first"]


def fix(s):
    if isinstance(s, str) and re.search(r"Ã.|â€", s):
        try:
            return s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def key(s):
    s = "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def main():
    countries = {json.loads(l)["id"]: json.loads(l)["countries"] for l in open(SRC / "snippets.jsonl")}
    snippets = {json.loads(l)["id"]: json.loads(l)["snippet"] for l in open(SRC / "snippets.jsonl")}
    raw = [json.loads(l) for f in sorted(glob.glob(str(SRC / "extracted_*.jsonl"))) for l in open(f)]
    legit = [r for r in raw if re.search(r"sin v[ií]ctimas|oferta formal", r.get("paraphrase", ""), re.I)]
    rows = [r for r in raw if r not in legit]

    groups = {}
    for r in rows:
        s_ = snippets.get(r["article_id"], "")
        if r["verbatim_quote"] and r["verbatim_quote"] not in s_ and r["verbatim_quote"] not in fix(s_):
            r["verbatim_quote"] = ""  # cita que no aparece literal en la fuente: se descarta
        r = {k: fix(v) for k, v in r.items()}
        k = (key(r["job_title"])[:40], r.get("pay_amount"), key(r["platform"]), key(r["offer_location"])[:30],
             key(r["verbatim_quote"])[:60])
        g = groups.setdefault(k, {"items": []})
        g["items"].append(r)

    out, sources = [], []
    for i, g in enumerate(groups.values(), 1):
        best = max(g["items"], key=lambda r: ({"high": 2, "medium": 1, "low": 0}[r["confidence"]], len(r["verbatim_quote"])))
        ctry = sorted({c for r in g["items"] for c in countries.get(r["article_id"], [])})
        o = {f: best.get(f, "") for f in FIELDS}
        o.update({
            "offer_uid": f"PRESS-{i:04d}", "n_sources": len({r['url'] for r in g['items']}),
            "countries": ";".join(ctry),
            "type_a_flags": ";".join(best.get("type_a_flags") or []),
            "type_b_flags": ";".join(best.get("type_b_flags") or []),
            "outlets": ";".join(sorted({r["outlet"] for r in g["items"]})),
            "urls": " ".join(sorted({r["url"] for r in g["items"]})),
            "published_first": min(r["published"] for r in g["items"]),
        })
        out.append(o)
        seen = set()
        for r in g["items"]:
            if r["url"] not in seen:
                seen.add(r["url"])
                sources.append({"offer_uid": o["offer_uid"], "url": r["url"], "outlet": r["outlet"], "published": r["published"]})

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "press_offers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    with open(OUT / "press_offer_sources.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["offer_uid", "url", "outlet", "published"])
        w.writeheader()
        w.writerows(sources)

    mx = [o for o in out if "MEX" in o["countries"]]
    stats = {
        "extracted_raw": len(raw), "legit_excluded": len(legit), "unique_offers": len(out), "mexico": len(mx),
        "with_verbatim_quote": sum(1 for o in out if o["verbatim_quote"]),
        "confidence": Counter(o["confidence"] for o in out),
        "platform_mx": Counter(o["platform"] or "no_dice" for o in mx).most_common(),
        "scheme_mx": Counter(o["scheme"] for o in mx).most_common(),
        "criminal_recruitment_mx": sum(1 for o in mx if o["criminal_recruitment"] is True),
        "type_a_flags_mx": Counter(f for o in mx for f in o["type_a_flags"].split(";") if f).most_common(),
        "type_b_flags_mx": Counter(f for o in mx for f in o["type_b_flags"].split(";") if f).most_common(),
        "outcome_mx": Counter(o["outcome"] or "no_dice" for o in mx).most_common(),
    }
    (OUT / "press_offers_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
