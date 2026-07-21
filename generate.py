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
BASE_URL = os.environ.get("BASE_URL", "https://about.veidapp.no")   # <-- bytt til din faktiske URL, eller sett som repo-variabel BASE_URL i GitHub Actions
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
    <a class="logo" href="{p}index.html"><span class="badge">🔧</span>VEIDapp · Servicebok og feildatabase</a>
    <nav>
      <a href="{p}index.html">Bla i merker</a>
      <a href="{p}index.html#slik-fungerer-det">Slik fungerer det</a>
      <a class="btn-cta" href="{APP_URL}" rel="noopener" target="_blank">Prøv appen!</a>
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
<section class="search-section">
  <div class="wrap">
    <div class="search-box">
      <input id="search-input" type="text" placeholder="Søk f.eks. «Claas Arion», «Valtra startproblemer», «ID0251» …" autocomplete="off">
      <div id="search-results"></div>
    </div>
  </div>
</section>

<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Feilsøking · Servicelogg · Vedlikehold</p>
      <h1>Finn feilkoder. Søk i feilhistorikker. Digital servicebok.</h1>
      <p class="lead">

<p>VEIDapp er en frivillig drevet tjeneste, som blir bedre for hver feil som deles. Logg service, følg historikk og finn løsninger raskere 
— for kjøretøy, maskiner, bygg og utstyr.</p>

<p>Vi håper du kan få hjelp av appen, og bidra med din kunnskap, slik at andre kan få din hjelp! VEIDapp er ingenting uten din kunnskap!</p>
    
      <div class="hero-actions">
        <a class="btn-cta" href="{APP_URL}" rel="noopener" target="_blank">Prøv VEIDapp GRATIS</a>
        <a class="btn-ghost" style="color:var(--ink);border-color:var(--line)" href="#merker">Bla i merker</a>
      </div>
      <div class="stat-row">
        <div class="stat"><b>{TOTAL}+</b><span>Feilrapporter</span></div>
        <div class="stat"><b>{TOTAL_BRANDS}</b><span>Merker</span></div>
        <div class="stat"><b>{TOTAL_MODELS}+</b><span>Modeller</span></div>
      </div>
    </div>
   <div>
      <div class="service-preview">
        <p class="sp-label">Eksempel · Servicevarsel</p>
        <div class="sp-row">
          <div class="sp-thumb">🚜</div>
          <div class="sp-info">
            <p class="sp-reg">AB1234 · Rammenummer XXX</p>
            <p class="sp-title">2012 Valtra N141</p>
            <p class="sp-service">Forrige service: 14. mars 2026</p>
            <p class="sp-service sp-due">Neste service innen: 15. september 2026</p>
          </div>
          <div class="sp-arrow">›</div>
        </div>
      </div>
      <div class="readout" style="margin-top:14px">
        <p class="rlabel">Eksempel · {esc(example['brand'])} {esc(example['model'])}</p>
        <p class="rcode">{esc(example['feilkode']) or '—'}</p>
        <p class="rsymptom">{esc(example['symptom_display'])}</p>
        <div class="rmeta">
          <span>{esc(example['vtype'] or 'Kjøretøy')}</span>
          <span>{esc(example['feiltype'] or 'Feiltype')}</span>
          <span>{esc(example['year'] or 'Årsmodell')}</span>
        </div>
        <div class="locked">🔒 Full løsning + servicelogg i VEIDapp</div>
      </div>
    </div>
  </div>
</section>

<section class="section" id="slik-fungerer-det">
  <div class="wrap">
    <div class="section-head"><h2>Slik fungerer det</h2></div>
    <div class="steps">
      <div class="step"><div class="num">01</div><h3>Søk feilkode eller symptom</h3><p>Finn kjøretøyet, maskinen eller feilkoden du sliter med — på tvers av bil, traktor, skurtresker og anleggsutstyr.</p></div>
      <div class="step"><div class="num">02</div><h3>Se hva andre har opplevd</h3><p>Sammenlign symptomer og feiltyper andre brukere har registrert på samme merke og modell.</p></div>
      <div class="step"><div class="num">03</div><h3>Full servicehistorikk</h3><p>Loggfør servicer og få påminnelser i VEIDapp — bygget av og for de som faktisk skrur.</p></div>
    </div>
  </div>
</section>

<section class="section" id="merker">
  <div class="wrap">
    <div class="section-head">
      <h2>Bla i merker</h2>
      <span class="note">Sortert etter antall rapporter</span>
    </div>
    <div class="brand-grid">
      {brand_cards}
    </div>
  </div>
</section>

<section class="cta-band">
  <div class="wrap">
    <h2>Bygg Norges beste feilsøkingsdatabase — sammen med oss</h2>
    <p>VEIDapp er GRATIS og frivillig, og blir bedre for hver feil som deles. Logg service, følg historikk og finn løsninger raskere — for kjøretøy, maskiner, bygg og utstyr.</p>
    <a class="btn-cta" href="{APP_URL}" rel="noopener" target="_blank">Prøv VEIDapp gratis →</a>
  </div>
</section>
'''

schema_home = {
  "@context":"https://schema.org",
  "@type":"WebSite",
  "name":"VEIDapp Feilkodedatabase",
  "url": BASE_URL,
  "description":"Feilsøkingsdatabase for kjøretøy, traktorer og maskiner i Norge.",
  "potentialAction":{
    "@type":"SearchAction",
    "target": f"{BASE_URL}/index.html?q={{search_term_string}}",
    "query-input":"required name=search_term_string"
  }
}

with open(os.path.join(OUT,"index.html"), "w", encoding="utf-8") as f:
    f.write(page(
        "VEIDapp Feilkodedatabase — feilkoder, symptomer og servicehistorikk",
        f"Søk blant {TOTAL}+ ekte feilrapporter fra traktor, bil, skurtresker og maskiner. Se feilkoder og symptomer — full løsning i VEIDapp.",
        "/index.html", home_body, depth=0,
        extra_head='<script defer src="search.js"></script>',
        schema=schema_home
    ))

print("Forside generert.")
print(f"Totalt {TOTAL} rapporter, {TOTAL_BRANDS} merker, {TOTAL_MODELS} modeller.")

# =========================================================
# MERKESIDER
# =========================================================
sitemap_urls = [("/index.html", "1.0")]

for b in brands_sorted:
    slug = slugify(b)
    b_entries = by_brand[b]
    b_models = sorted(set(e["model"] for e in b_entries if e["model"]))
    outdir = os.path.join(OUT, "merker", slug)
    os.makedirs(outdir, exist_ok=True)

    rows_html = ""
    for e in sorted(b_entries, key=lambda x: (x["model"], x["symptom_display"])):
        code_pill = f'<span class="rcode-pill">{esc(e["feilkode"])}</span>' if e["feilkode"] else '<span class="rcode-pill" style="color:var(--steel)">Se detaljer</span>'
        model_bit = f'{esc(e["model"])} · ' if e["model"] else ''
        rows_html += f'''<a class="report-row" href="{e['slug']}.html">
          <div>
            <p class="rtitle">{model_bit}{esc(e['symptom_display'])}</p>
            <p class="rtags">{esc(e['vtype'] or '')} · {esc(e['feiltype'] or '')} · {esc(e['year'] or 'Årsmodell ukjent')}</p>
          </div>
          {code_pill}
        </a>'''

    models_note = f"{len(b_models)} modeller registrert" if b_models else "Merke uten spesifikk modellinndeling"

    body = f'''
<div class="wrap">
  <p class="crumbs"><a href="../../index.html">Hjem</a><span class="sep">/</span>{esc(b)}</p>
</div>
<section class="hero" style="padding:34px 0 30px">
  <div class="wrap">
    <p class="eyebrow">Merke</p>
    <h1>{esc(b)} — feilkoder og feilsøking</h1>
    <p class="lead">{len(b_entries)} registrerte feilrapporter for {esc(b)}. {models_note}. Se symptom og feilkode her — full løsning og servicehistorikk finner du i VEIDapp.</p>
    <div class="hero-actions">
      <a class="btn-cta" href="{APP_URL}" rel="noopener" target="_blank">Prøv VEIDapp gratis</a>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="section-head"><h2>Alle rapporter — {esc(b)}</h2><span class="note">{len(b_entries)} stk</span></div>
    <div class="report-list">
      {rows_html}
    </div>
  </div>
</section>
'''
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(
            f"{b} feilkoder og feilsøking — {len(b_entries)} rapporter | VEIDapp",
            f"Se registrerte feilkoder, symptomer og feiltyper for {b}. {len(b_entries)} feilrapporter fra virkelige brukere. Full løsning i VEIDapp.",
            f"/merker/{slug}/index.html", body, depth=2
        ))
    sitemap_urls.append((f"/merker/{slug}/index.html", "0.7"))

print(f"{TOTAL_BRANDS} merkesider generert.")

# =========================================================
# DETALJSIDER (én per feilrapport)
# =========================================================
teaser_search = []

for e in entries:
    slug = e["slug"]; brand_slug = e["brand_slug"]
    outdir = os.path.join(OUT, "merker", brand_slug)
    os.makedirs(outdir, exist_ok=True)

    tags = []
    if e["vtype"]: tags.append(e["vtype"])
    if e["year"]: tags.append(f"Årsmodell {e['year']}")
    if e["feiltype"]: tags.append(e["feiltype"])
    if e["symkat"]: tags.append(e["symkat"])
    tag_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)

    teaser_context = truncate_words(e["kommentar"], 30) if e["kommentar"] else ""
    solution_len = len(e["losning"].split())

    related = [r for r in by_brand[e["brand"]] if r["slug"] != slug][:5]
    if related:
        related_items = []
        for r in related:
            code_bit = ""
            if r["feilkode"]:
                code_bit = " · " + esc(r["feilkode"])
            related_items.append(
                '<li><a href="' + r["slug"] + '.html">' + esc(r["symptom_display"]) + code_bit + '</a></li>'
            )
        related_html = "".join(related_items)
    else:
        related_html = "<li>Ingen flere rapporter for dette merket ennå.</li>"

    model_title = f"{esc(e['brand'])} {esc(e['model'])}" if e["model"] else esc(e['brand'])

    body = f'''
<div class="wrap">
  <p class="crumbs"><a href="../../index.html">Hjem</a><span class="sep">/</span><a href="index.html">{esc(e['brand'])}</a><span class="sep">/</span>{esc(e['symptom_display'])}</p>
</div>

<section class="section" id="slik-fungerer-det">
  <div class="wrap">
    <div class="section-head"><h2>Slik fungerer det</h2></div>
    <div class="steps">
      <div class="step"><div class="num">01</div><h3>Søk feilkode eller symptom</h3><p>Finn kjøretøyet, maskinen eller feilkoden du sliter med — på tvers av bil, traktor, skurtresker og anleggsutstyr.</p></div>
      <div class="step"><div class="num">02</div><h3>Se hva andre har opplevd</h3><p>Sammenlign symptomer og feiltyper andre brukere har registrert på samme merke og modell.</p></div>
      <div class="step"><div class="num">03</div><h3>Full servicehistorikk</h3><p>Loggfør servicer og få påminnelser i VEIDapp — bygget av og for de som faktisk skrur.</p></div>
    </div>
  </div>
</section>


<div class="wrap detail-head">
  <p class="eyebrow">{esc(e['brand'])}{" · " + esc(e['model']) if e['model'] else ""}</p>
  <h1 style="font-size:2rem">{esc(e['symptom_display'])}</h1>
  <div class="tagrow">{tag_html}</div>
</div>
<div class="wrap detail-body">
  <div class="context">
    <div class="readout" style="margin-bottom:26px">
      <p class="rlabel">Feilkode</p>
      <p class="rcode">{esc(e['feilkode']) or 'Ingen registrert feilkode'}</p>
      <p class="rsymptom">{esc(e['symptom_display'])}</p>
      <div class="rmeta">
        <span>{esc(e['vtype'] or 'Kjøretøy')}</span>
        <span>{esc(e['feiltype'] or 'Feiltype')}</span>
      </div>
    </div>
    <h3>Hva ble observert</h3>
    <p>{esc(teaser_context) or 'Symptom registrert av bruker i VEIDapp sin feilsøkingsdatabase, uten ytterligere kommentar.'}</p>

    <div class="related">
      <h3>Flere rapporter for {esc(e['brand'])}</h3>
      <ul>{related_html}</ul>
    </div>
  </div>

  <aside class="gate">
    <p class="glabel">Løsning</p>
    <div class="lock">🔒 Låst innhold</div>
    <p class="gblur">{esc(truncate_words(e['losning'], 18)) or 'Løsning registrert i VEIDapp av bruker som har fikset dette selv.'}</p>
    <p class="gcta">{solution_len}+ ord med konkret løsning, deler/komponenter og fremgangsmåte er tilgjengelig gratis i VEIDapp — sammen med servicelogg og påminnelser for dette kjøretøyet.</p[...]
    <a class="btn-cta" href="{APP_URL}" rel="noopener" target="_blank">Se full løsning i VEIDapp</a>
  </aside>
</div>
'''
    schema = {
        "@context":"https://schema.org",
        "@type":"TechArticle",
        "headline": e["title"][:110],
        "description": f"Feilrapport for {model_title}: {e['symptom_display']}. {teaser_context}"[:300],
        "about": model_title,
        "proficiencyLevel":"Beginner"
    }

    with open(os.path.join(outdir, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(page(
            f"{e['title']} | VEIDapp",
            (f"{model_title} — {e['symptom_display']}. " + (f"Feilkode: {e['feilkode']}. " if e['feilkode'] else "") + "Se symptom her, full løsning i VEIDapp.")[:158],
            e["url"], body, depth=2, schema=schema
        ))
    sitemap_urls.append((e["url"], "0.5"))
    teaser_search.append({
        "t": e["title"], "b": e["brand"], "m": e["model"], "code": e["feilkode"],
        "s": e["symptom_display"], "u": e["url"]
    })

print(f"{TOTAL} detaljsider generert.")

with open(os.path.join(OUT, "data", "teaser.json"), "w", encoding="utf-8") as f:
    json.dump(teaser_search, f, ensure_ascii=False)

# =========================================================
# sitemap.xml + robots.txt
# =========================================================
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, prio in sitemap_urls:
    sm.append(f"  <url><loc>{BASE_URL}{path}</loc><priority>{prio}</priority></url>")
sm.append("</urlset>")
with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write("\n".join(sm))

with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

print("sitemap.xml og robots.txt generert.")
print("FERDIG.")
