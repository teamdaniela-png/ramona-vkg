#!/usr/bin/env python3
"""
Ramona press scraper.

Pulls Spanish-language news about human-trafficking recruitment, fake job offers
and disappearances from Google News RSS, then fetches each article and extracts
clean text with trafficatura. Writes one JSONL record per article.

Usage:
    python scripts/scrape_press.py --out data/raw/press.jsonl [--max-per-query 100]

Designed to be resumable. If the output file exists, it is loaded and already-seen
URLs are skipped.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import feedparser
import requests
import trafilatura
from googlenewsdecoder import gnewsdecoder

UA = "RamonaObservatorio/1.0 (+https://ramonaaliadalaboral.com)"

QUERIES = [
    # core trafficking + recruitment
    '"trata de personas" reclutamiento',
    '"oferta de trabajo" falsa trata',
    '"oferta laboral" falsa fraude',
    '"reclutamiento" redes sociales trata',
    '"facebook marketplace" trata',
    '"whatsapp" reclutamiento trata',
    '"telegram" reclutamiento trata',
    # disappearance linked to job offer
    '"desapareció" "oferta de trabajo"',
    '"desaparecida" "entrevista de trabajo"',
    '"desaparecido" "cita de trabajo"',
    '"se fue a una entrevista" desapareció',
    '"no regresó" "oferta de trabajo"',
    # specific documented cases
    '"rancho izaguirre" reclutamiento',
    '"edith guadalupe" trata',
    '"edificio revolución 829"',
    '"hotel" reclutamiento trata jalisco',
    # country-specific Mexico
    '"trata de personas" México',
    '"trata laboral" México',
    '"reclutamiento CJNG" jalisco',
    '"reclutamiento forzado" cartel',
    '"seguridad privada" reclutamiento trata',
    '"víctimas de trata" México',
    '"explotación laboral" México',
    # other LatAm (Spanish)
    '"trata de personas" Colombia',
    '"trata de personas" Perú',
    '"trata de personas" Argentina',
    '"trata de personas" Chile',
    '"trata de personas" Ecuador',
    '"trata de personas" Bolivia',
    '"trata de personas" Venezuela',
    '"trata de personas" Guatemala',
    '"trata de personas" Honduras',
    '"trata de personas" "El Salvador"',
    '"trata de personas" Paraguay',
    '"trata de personas" "República Dominicana"',
    '"oferta de trabajo" falsa Colombia',
    '"oferta de trabajo" falsa Argentina',
    '"oferta laboral" falsa Perú',
    # Brazil (Portuguese)
    '"tráfico de pessoas" recrutamento',
    '"vaga de emprego" falsa golpe',
    '"oferta de emprego" tráfico Brasil',
    '"trabalho escravo" aliciamento',
    # Spain
    '"trata de personas" España oferta trabajo',
    '"oferta de empleo" falsa estafa España',
    # platforms / channels
    '"instagram" reclutamiento trata',
    '"tiktok" reclutamiento trata',
    '"computrabajo" estafa oferta',
    '"indeed" oferta falsa estafa',
    '"linkedin" oferta falsa estafa',
    '"olx" oferta trabajo estafa',
    # exploitation types
    '"explotación sexual" reclutamiento',
    '"explotación laboral" oferta trabajo',
    '"trabajo doméstico" trata explotación',
    '"mendicidad forzada" trata',
    '"servidumbre" trata laboral',
    '"matrimonio forzado" trata',
    '"trabajo agrícola" explotación trata',
    '"call center" reclutamiento engaño',
    # modus operandi / lures
    '"modelo webcam" engaño trata',
    '"azafata" oferta falsa trata',
    '"niñera" extranjero estafa trata',
    '"trabajo en el extranjero" estafa reclutamiento',
    '"visa de trabajo" fraude reclutamiento',
    '"crucero" oferta trabajo estafa',
    '"Dubái" trabajo engaño trata',
    '"sueldo alto" "sin experiencia" estafa empleo',
    '"empleo bien pagado" desaparición',
    # cyber-trafficking / pig butchering / scam centers
    '"estafa laboral" criptomonedas reclutamiento',
    '"trabajo remoto" estafa secuestro',
    '"centro de estafas" reclutamiento latinoamericano',
    '"Camboya" OR "Myanmar" trabajo engaño latinoamericanos',
    '"fraude" oferta empleo redes sociales',
]


def gnews_rss_url(query: str, lang: str = "es-419", gl: str = "MX", ceid: str = "MX:es-419") -> str:
    return (
        f"https://news.google.com/rss/search?q={quote_plus(query)}"
        f"&hl={lang}&gl={gl}&ceid={ceid}"
    )


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen = set()
    with path.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("url"):
                    seen.add(rec["url"])
            except Exception:
                pass
    return seen


def resolve_gnews(url: str) -> str | None:
    """Decode a news.google.com/rss/articles/... URL to the real publisher URL."""
    if "news.google.com" not in url:
        return url
    try:
        r = gnewsdecoder(url, interval=1)
        if r.get("status") and r.get("decoded_url"):
            return r["decoded_url"]
    except Exception:
        pass
    return None


def fetch_article(url: str, timeout: int = 20) -> tuple[str | None, str | None]:
    """Return (clean_text, final_url) or (None, None) on failure."""
    real_url = resolve_gnews(url) or url
    try:
        r = requests.get(real_url, headers={"User-Agent": UA}, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            return None, r.url
        final_url = r.url
        text = trafilatura.extract(
            r.text,
            include_comments=False,
            include_tables=False,
            favor_recall=False,
            deduplicate=True,
        )
        return text, final_url
    except Exception:
        return None, real_url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw/press.jsonl")
    ap.add_argument("--max-per-query", type=int, default=100)
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen = load_seen(out_path)
    print(f"[press] starting. already seen: {len(seen)}")

    written = 0
    with out_path.open("a") as out:
        for q in QUERIES:
            url = gnews_rss_url(q)
            print(f"[press] query: {q}")
            try:
                feed = feedparser.parse(url)
            except Exception as e:
                print(f"[press] feed error: {e}")
                continue
            entries = feed.entries[: args.max_per_query]
            print(f"[press]   {len(entries)} items in feed")
            for e in entries:
                link = e.get("link")
                if not link or link in seen:
                    continue
                seen.add(link)
                title = e.get("title", "").strip()
                outlet = None
                if "source" in e and hasattr(e.source, "title"):
                    outlet = e.source.title
                elif " - " in title:
                    outlet = title.rsplit(" - ", 1)[-1]
                pub = e.get("published", "")
                text, final_url = fetch_article(link)
                rec = {
                    "id": sha1(link),
                    "query": q,
                    "title": title,
                    "outlet": outlet,
                    "published": pub,
                    "url": link,
                    "final_url": final_url,
                    "domain": urlparse(final_url).netloc if final_url else None,
                    "text": text,
                    "scraped_ok": bool(text),
                    "chars": len(text) if text else 0,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                written += 1
                if written % 20 == 0:
                    print(f"[press] written so far: {written}")
                time.sleep(args.sleep)
    print(f"[press] done. new records: {written}. total unique urls: {len(seen)}")


if __name__ == "__main__":
    main()
