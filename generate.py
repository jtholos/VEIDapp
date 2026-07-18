#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genererer en statisk nettside (for GitHub Pages) fra VEIDapp sin
feilrapport-CSV. Viser feilkoder/symptomer som "smakebiter" og
gjemmer selve løsningen bak en CTA til appen.
"""
import csv, re, os, html, json, shutil
from collections import defaultdict, Counter

CSV_PATH = os.environ.get("CSV_PATH", "data/feilrapporter.csv")
OUT = os.environ.get("OUT_DIR", "public")
BASE_URL = os.environ.get("BASE_URL", "https://feilkoder.veidapp.no")   # <-- bytt til din faktiske URL, eller sett som repo-variabel BASE_URL i GitHub Actions
APP_URL = "https://www.veidapp.no/"

os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "merker"), exist_ok=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

# kopier statiske filer (styles.css, search.js) inn i output-mappen
for fname in ("styles.css", "search.js"):
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(OUT, fname))

def slugify(s):
    s = s.strip().lower()
    repl = {"æ":"ae","ø":"o","å":"aa","é":"e","è":"e","ü":"u"}
    for k,v in repl.items():
        s = s.replace(k,v)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "na"

def esc(s):
    return html.escape((s or "").strip())

def truncate_words(s, n=26):
    s = (s or "").strip()
    words = s.split()
    if len(words) <= n:
        return s
    return " ".join(words[:n]) + " …"

with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# ---- normaliser og berik rader ----
brand_counter = Counter()
per_brand_slug_counter = Counter()
entries = []
for i, row in enumerate(rows):
    brand = row["Merke"].strip()
    if not brand:
        continue
    model = row["Modell"].strip()
    vtype = row["Type kjøretøy"].strip()
    year = row["Årsmodell"].strip()
    feiltype = row["Feiltype"].strip()
    symkat = row["Symptomkategori"].strip()
    symvalg = row["Symptom (valg)"].strip()
    symdetalj = row["Symptomdetalj (manuell)"].strip()
    kommentar = row["Kommentar"].strip()
    losning = row["Løsning"].strip()
    feilkode = row["Feilkode"].strip()

    symptom_display = symvalg or symdetalj or symkat or feiltype or "Ukjent symptom"

    brand_slug = slugify(brand)
    model_slug = slugify(model) if model else "generell"
    per_brand_slug_counter[brand_slug] += 1
    n = per_brand_slug_counter[brand_slug]
    base_slug = f"{model_slug}-{slugify(feiltype) or 'feil'}-{n}"

    title_bits = [brand]
    if model: title_bits.append(model)
    title = " ".join(title_bits) + " – " + symptom_display
    if feilkode:
        title += f" (feilkode {feilkode})"

    entries.append(dict(
        brand=brand, brand_slug=brand_slug, model=model, model_slug=model_slug,
        vtype=vtype, year=year, feiltype=feiltype, symkat=symkat,
        symptom_display=symptom_display, kommentar=kommentar, losning=losning,
        feilkode=feilkode, slug=base_slug, title=title,
        url=f"/merker/{brand_slug}/{base_slug}.html"
    ))
    brand_counter[brand] += 1

brands_sorted = [b for b,_ in brand_counter.most_common()]
by_brand = defaultdict(list)
for e in entries:
    by_brand[e["brand"]].append(e)

TOTAL = len(entries)
TOTAL_BRANDS = len(brands_sorted)
TOTAL_MODELS = len(set((e["brand"], e["model"]) for e in entries if e["model"]))

# ---- felles HTML-biter ----
HEAD_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&'
    'family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" '
    'rel="stylesheet">'
)

def header(depth=0):
    p = "../" * depth
    return f'''<header class="site-header">
  <div class="wrap">
    <a class="logo" href="{p}index.html"><span class="badge">🔧</span>VEID<span style="color:var(--green)">app</span> · Feilkodedatabase</a>
    <nav>
      <a href="{p}index.html">Bla i merker</a>
      <a href="{p}index.html#slik-fungerer-det">Slik fungerer det</a>
      <a class="btn-cta" href="{APP_URL}" rel="noopener" target="_blank">Prøv appen gratis</a>
    </nav>
  </div>
</header>'''

def footer(depth=0):
    p = "../" * depth
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div>© {2026} VEIDapp · Bygget av brukere, for brukere.</div>
    <div><a href="mailto:kontakt@VEIDapp.no">kontakt@VEIDapp.no</a> · <a href="{APP_URL}" rel="noopener" target="_blank">Åpne VEIDapp</a></div>
  </div>
</footer>'''

def page(title, description, canonical_path, body, depth=0, extra_head="", schema=None):
    canonical = f"{BASE_URL}{canonical_path}"
    schema_tag = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    return f'''<!DOCTYPE html>
<html lang="no">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
{HEAD_FONTS}
<link rel="stylesheet" href="{'../'*depth}styles.css">
{extra_head}
{schema_tag}
</head>
<body>
{header(depth)}
{body}
{footer(depth)}
</body>
</html>'''

# =========================================================
# FORSIDE
# =========================================================
example = entries[0]
for e in entries:
    if e["feilkode"]:
        example = e
        break

brand_cards = ""
for b in brands_sorted:
    count = brand_counter[b]
    slug = slugify(b)
    brand_cards += f'''<a class="brand-card" href="merker/{slug}/index.html">
      <div class="bname">{esc(b)}</div>
      <div class="bcount">{count} feilrapporter</div>
    </a>'''

home_body = f'''
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Feilsøking · Servicelogg · Vedlikehold</p>
      <h1>Finn feilkoden. Skjønn symptomet. Fiks det riktig.</h1>
      <p class="lead">VEIDapp samler ekte feilrapporter fra traktorer, maskiner og kjøretøy i Norge — feilkoder, symptomer og faktiske løsninger andre har brukt. Denne siden viser et utvalg av databasen. Full løsning finner du i appen.</p>
      <div class="hero-actions">
        <a class="btn-cta" href="{APP_URL}" rel="noopener" target="_blank">Prøv VEIDapp gratis</a>
        <a class="btn-ghost" style="color:var(--ink);border-color:var(--line)" href="#merker">Bla i merker</a>
      </div>
      <div class="stat-row">
        <div class="stat"><b>{TOTAL}+</b><span>Feilrapporter</span></div>
        <div class="stat"><b>{TOTAL_BRANDS}</b><span>
