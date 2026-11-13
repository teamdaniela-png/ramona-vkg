#!/usr/bin/env python3
"""
Scraper of the public figures of the Consejo Ciudadano para la Seguridad y Justicia de la Ciudad
de México (consejociudadanomx.org) on fake job offers, labour fraud, trafficking and recruitment.

Sources: (1) bulletins /boletines?page=N -> /contenido/<slug>; (2) PDF reports in /reportes.
One request per second, with a local cache.

Outputs:
  data/raw/consejo/html/*.html, data/raw/consejo/pdf/*.pdf     (cache, git-ignored)
  data/processed/consejo/documentos_relevantes.jsonl           (text, git-ignored)
  data/processed/consejo/cifras_consejo.csv                    (sentences with figures and their source)

Usage: python3 scripts/scrape_consejo_ciudadano.py [--max-pages 60] [--no-pdf]
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://consejociudadanomx.org"
RAW = ROOT / "data/raw/consejo"
OUT = ROOT / "data/processed/consejo"
UA = {"User-Agent": "Mozilla/5.0 (research; RATR-O, TU Wien; contact: daniela@ramonaaliadalaboral.com)"}

# Tema: ofertas de trabajo falsas y lo que cuelga de ellas
TOPIC = re.compile(
    r"(ofertas? (falsas? )?de (empleo|trabajo)|empleos? falsos?|trabajos? falsos?|fraude laboral|"
    r"vacantes? falsas?|reclutamiento|recluta|trata de personas|explotaci[oó]n laboral|enganche|"
    r"montadeudas|pago por adelantado para (un )?empleo|bolsa de trabajo)", re.I)
NUM = re.compile(r"\d|\b(mil|millones?|cien|ciento)\b", re.I)
SENT = re.compile(r"(?<=[\.\!\?;])\s+")
MONTHS = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
DATE = re.compile(r"\b(\d{1,2}) (?:de )?(" + "|".join(MONTHS) + r")(?: de)? (\d{4})", re.I)


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def get(session, url, path, binary=False):
    if path.exists():
        return path.read_bytes() if binary else path.read_text(encoding="utf-8", errors="replace")
    for attempt in range(3):
        time.sleep(1.0 + 2 * attempt)
        try:
            r = session.get(url, headers=UA, timeout=120)
            break
        except requests.RequestException as e:
            print(f"  reintento {attempt + 1} {url}: {type(e).__name__}", flush=True)
    else:
        print(f"  OMITIDO tras 3 intentos: {url}", flush=True)
        return None
    if r.status_code != 200:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        path.write_bytes(r.content)
        return r.content
    path.write_text(r.text, encoding="utf-8")
    return r.text


def iso_date(text):
    m = DATE.search(norm(text.lower()))
    if not m:
        return ""
    d, mo, y = m.groups()
    return f"{y}-{MONTHS.index(mo.lower()) + 1:02d}-{int(d):02d}"


def figure_sentences(text):
    out = []
    for s in SENT.split(re.sub(r"\s+", " ", text)):
        if TOPIC.search(s) and NUM.search(s) and 30 < len(s) < 700:
            out.append(s.strip())
    return out


def crawl_boletines(session, max_pages):
    links = {}
    for p in range(1, max_pages + 1):
        h = get(session, f"{BASE}/boletines?page={p}", RAW / "html" / f"boletines_p{p:03d}.html")
        if not h:
            break
        found = set(re.findall(r'href="(https://consejociudadanomx\.org/contenido/[^"]+)"', h))
        if not found:
            break
        for u in found:
            links.setdefault(u, p)
    return links


def read_boletin(session, url):
    slug = url.rsplit("/", 1)[-1]
    h = get(session, url, RAW / "html" / f"{slug[:150]}.html")
    if not h:
        return None
    b = BeautifulSoup(h, "html.parser")
    title = (b.find("h1").get_text(" ", strip=True) if b.find("h1") else slug)
    art = b.find("article")
    body = art.get_text(" ", strip=True) if art else ""
    return {"source": "boletin", "url": url, "title": title, "date": iso_date(body[:200]) or iso_date(b.get_text(" ")[:3000]),
            "text": body}


def read_pdfs(session):
    h = get(session, f"{BASE}/reportes", RAW / "html" / "reportes.html")
    docs = []
    for href in sorted(set(re.findall(r'href="(/media/pdf/[^"]+\.pdf)"', h or ""))):
        url = urljoin(BASE, href)
        name = hashlib.sha1(url.encode()).hexdigest()[:10] + "_" + re.sub(r"[^\w\.-]", "_", unquote(href.rsplit("/", 1)[-1]))
        pdf = RAW / "pdf" / name
        if get(session, url, pdf, binary=True) is None:
            continue
        txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
        docs.append({"source": "reporte_pdf", "url": url, "title": unquote(href.rsplit("/", 1)[-1]),
                     "date": iso_date(txt[:3000]), "text": txt})
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=60)
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()

    links = crawl_boletines(s, args.max_pages)
    print(f"boletines encontrados: {len(links)}", flush=True)
    docs = []
    for i, u in enumerate(sorted(links), 1):
        d = read_boletin(s, u)
        if d:
            docs.append(d)
        if i % 50 == 0:
            print(f"  leidos {i}/{len(links)}", flush=True)
    if not args.no_pdf:
        pdfs = read_pdfs(s)
        print(f"reportes PDF: {len(pdfs)}", flush=True)
        docs += pdfs

    relevant = [d for d in docs if TOPIC.search(d["title"] + " " + d["text"])]
    with open(OUT / "documentos_relevantes.jsonl", "w", encoding="utf-8") as f:
        for d in relevant:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    rows = []
    for d in relevant:
        for sent in figure_sentences(d["text"]):
            topic = sorted({m.group(0).lower() for m in TOPIC.finditer(sent)})
            rows.append({"date": d["date"], "source": d["source"], "title": d["title"][:200], "url": d["url"],
                         "topic_terms": "; ".join(topic), "sentence": sent})
    with open(OUT / "cifras_consejo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "source", "title", "url", "topic_terms", "sentence"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["date"]))
    print(f"documentos totales {len(docs)} | relevantes {len(relevant)} | frases con cifras {len(rows)}")


if __name__ == "__main__":
    main()
