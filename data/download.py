# /// script
# requires-python = ">=3.12"
# ///
"""Télécharge un échantillon d'URD (Documents d'Enregistrement Universel) du CAC 40
depuis info-financiere.gouv.fr (information réglementée publique de l'AMF).

Source : API Opendatasoft "Explore v2.1" du dataset des flux AMF.
Doc API : https://info-financiere.gouv.fr/pages/api0/

Réalité du format (vérifiée via --discover) : contrairement à ce qu'on pourrait
attendre, l'URD n'est PAS distribué en PDF depuis l'exercice 2021. Les émetteurs
déposent désormais un paquet **ESEF** : une archive ZIP contenant un gros fichier
**xHTML (iXBRL)**. Seuls les plus anciens exercices existent encore en PDF.

Ce script :

1. Cherche les URD par **ISIN exact** (champ stable), pas par nom flou.
2. Filtre sur le **titre** pour ne garder que l'URD lui-même et écarter les avis
   "mise à disposition", amendements et rectificatifs.
3. Suit l'**URL directe** (`url_de_recuperation`) en conservant la vraie extension.
4. Pour un ZIP ESEF, **extrait le xHTML du rapport** (le plus volumineux).
5. Regroupe par **exercice** (année de publication − 1) et déduplique.

Découverte du schéma (lecture seule, ne télécharge rien) :

    uv run data/download.py --discover
"""
from __future__ import annotations

import io
import json
import shutil
import sys
import time
import unicodedata
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib import error, parse, request


# Params : édite-les, puis lance `uv run data/download.py`
USER_AGENT = "Assistant Financier votre.email@example.com"

# Émetteurs CAC 40 : nom affiché -> ISIN.
# Le filtrage se fait par ISIN (identifiant stable), le nom n'est qu'un libellé.
ISSUERS = {
    "LVMH": "FR0000121014",
    "TotalEnergies": "FR0000120271",
    "Sanofi": "FR0000120578",
    "L'Oreal": "FR0000120321",
    "Air Liquide": "FR0000120073",
}
# Exercices visés (année comptable couverte par l'URD).
# L'URD d'un exercice N est publié au T1 de l'année N+1.
TARGET_FISCAL_YEARS = set(range(2020, 2026))  # 2020–2025
OUTPUT_DIR = Path(__file__).resolve().parent / "downloads"
CLEAR_OUTPUT_DIR = True

API_BASE = "https://www.info-financiere.gouv.fr/api/explore/v2.1"
DATASET = "flux-amf-new-prod"
PAGE_SIZE = 100  # plafond Opendatasoft par page
FTP_BASE = "https://fr.ftp.opendatasoft.com/datadila/INFOFI/"

# Champs du dataset (confirmés via --discover).
FIELD_ISIN = "identificationsociete_iso_cd_isi"
FIELD_TITLE = "informationdeposee_inf_tit_inf"
FIELD_DATE = "informationdeposee_inf_dat_emt"  # date de transmission (ISO)
FIELD_URL = "url_de_recuperation"
FIELD_FILE = "fichierdecontenu_inf_fic_nom"
FIELD_COMPANY = "identificationsociete_iso_nom_soc"

# Le titre doit contenir cette phrase pour être un URD…
URD_PHRASE = "enregistrement universel"
# …et ne contenir aucun de ces termes : avis "mise à disposition", amendements,
# rectificatifs, et brochures d'assemblée générale qui citent l'URD dans leur titre.
TITLE_EXCLUDE = (
    "mise a disposition",
    "amendement",
    "rectificatif",
    "errata",
    "complement",
    "communique",
    "assemblee generale",
)

# Filet de sécurité : un URD complet pèse plusieurs Mo. En deçà, c'est un avis,
# une brochure ou un document tronqué — pas le document principal.
MIN_DOC_BYTES = 1_000_000


def get_json(url: str) -> dict:
    req = request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def get_bytes(url: str) -> bytes:
    req = request.Request(
        url,
        headers={"Accept": "application/octet-stream,*/*", "User-Agent": USER_AGENT},
    )
    with request.urlopen(req, timeout=300) as response:
        return response.read()


def records_url(where: str, limit: int, offset: int) -> str:
    query = parse.urlencode(
        {"where": where, "limit": limit, "offset": offset, "order_by": FIELD_DATE}
    )
    return f"{API_BASE}/catalog/datasets/{DATASET}/records?{query}"


def search_records(where: str, max_records: int = 1000) -> list[dict]:
    """Pagine l'API records et renvoie jusqu'à max_records enregistrements."""
    out: list[dict] = []
    offset = 0
    while len(out) < max_records and offset < 10000:
        page = get_json(records_url(where, PAGE_SIZE, offset))
        results = page.get("results", [])
        if not results:
            break
        out.extend(results)
        offset += PAGE_SIZE
    return out[:max_records]


def normalize(text: str) -> str:
    """Minuscule sans accents, pour comparer les titres de façon robuste."""
    folded = unicodedata.normalize("NFKD", text)
    return "".join(c for c in folded if not unicodedata.combining(c)).lower()


def is_urd_title(title: str) -> bool:
    norm = normalize(title)
    if URD_PHRASE not in norm:
        return False
    return not any(term in norm for term in TITLE_EXCLUDE)


def fiscal_year(record: dict) -> int | None:
    """Exercice couvert = année de publication − 1 (URD publié au T1 de N+1)."""
    raw = record.get(FIELD_DATE)
    if not isinstance(raw, str) or len(raw) < 4 or not raw[:4].isdigit():
        return None
    return int(raw[:4]) - 1


def source_url(record: dict) -> str | None:
    url = record.get(FIELD_URL)
    if isinstance(url, str) and url.startswith("http"):
        return url
    # Repli : reconstruire depuis le nom de fichier relatif.
    rel = record.get(FIELD_FILE)
    if isinstance(rel, str) and rel:
        return parse.urljoin(FTP_BASE, rel)
    return None


def url_extension(url: str) -> str:
    return url.lower().split("?")[0].rsplit(".", 1)[-1]


def extract_report_xhtml(zip_bytes: bytes) -> bytes | None:
    """Extrait le rapport xHTML (iXBRL) d'un paquet ESEF : le plus gros .xhtml/.html."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        pages = [
            info
            for info in archive.infolist()
            if info.filename.lower().endswith((".xhtml", ".html"))
        ]
        if not pages:
            return None
        biggest = max(pages, key=lambda info: info.file_size)
        return archive.read(biggest)


def select_filings(records: list[dict]) -> dict[int, dict]:
    """Garde un seul URD par exercice visé : le plus ancien (le dépôt d'origine)."""
    by_year: dict[int, dict] = {}
    for record in sorted(records, key=lambda r: r.get(FIELD_DATE, "")):
        if not is_urd_title(str(record.get(FIELD_TITLE, ""))):
            continue
        year = fiscal_year(record)
        if year is None or year not in TARGET_FISCAL_YEARS:
            continue
        by_year.setdefault(year, record)  # le tri ascendant garde le premier (origine)
    return by_year


def fetch_one(record: dict, name: str, year: int) -> tuple[Path, str] | None:
    """Télécharge un URD, gère le ZIP ESEF, renvoie (chemin local, format)."""
    url = source_url(record)
    if not url:
        return None
    ext = url_extension(url)
    try:
        payload = get_bytes(url)
    except error.HTTPError as exc:
        print(f"    échec {url}: {exc}")
        return None

    if ext == "zip":
        xhtml = extract_report_xhtml(payload)
        if xhtml is None:
            print(f"    ZIP sans rapport xHTML : {url}")
            return None
        payload, out_ext, fmt = xhtml, "xhtml", "esef-xhtml"
    elif ext in ("xhtml", "html", "xml"):
        out_ext, fmt = "xhtml", "esef-xhtml"
    elif ext == "pdf":
        out_ext, fmt = "pdf", "pdf"
    else:
        print(f"    format inattendu .{ext} : {url}")
        return None

    if len(payload) < MIN_DOC_BYTES:
        print(f"    ignoré ({len(payload) // 1024} Ko, trop petit pour un URD) : {url}")
        return None

    slug = "".join(c if c.isalnum() else "-" for c in name.lower())
    year_dir = OUTPUT_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    local_path = year_dir / f"{slug}_urd_{year}.{out_ext}"
    local_path.write_bytes(payload)
    return local_path, fmt


def discover() -> None:
    """Imprime le schéma du dataset et un enregistrement exemple."""
    meta = get_json(f"{API_BASE}/catalog/datasets/{DATASET}")
    fields = meta.get("dataset", {}).get("fields", meta.get("fields", []))
    print(f"Dataset: {DATASET}\nChamps:")
    for field in fields:
        print(f"  - {field.get('name')} ({field.get('type')}) — {field.get('label')}")
    sample = search_records(f'search({FIELD_TITLE},"{URD_PHRASE}")', 1)
    print("\nEnregistrement exemple:")
    print(json.dumps(sample[0] if sample else {}, indent=2, ensure_ascii=False))


def download_filings() -> dict:
    if CLEAR_OUTPUT_DIR and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source": "info-financiere.gouv.fr (AMF)",
        "dataset": DATASET,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "document_type": "URD (Document d'Enregistrement Universel)",
        "downloaded_count": 0,
        "filings": [],
    }

    for name, isin in ISSUERS.items():
        print(f"Recherche des URD de {name} ({isin})...")
        where = f'{FIELD_ISIN}="{isin}" and search({FIELD_TITLE},"{URD_PHRASE}")'
        selected = select_filings(search_records(where))

        for year in sorted(selected):
            record = selected[year]
            result = fetch_one(record, name, year)
            if result is None:
                continue
            local_path, fmt = result
            print(f"    exercice {year} : {fmt} -> {local_path.name}")
            manifest["filings"].append(
                {
                    "issuer": name,
                    "company": record.get(FIELD_COMPANY),
                    "isin": isin,
                    "document_type": "URD",
                    "fiscal_year": year,
                    "published_date": record.get(FIELD_DATE),
                    "title": record.get(FIELD_TITLE),
                    "source_format": fmt,
                    "source_url": source_url(record),
                    "local_path": str(local_path.relative_to(OUTPUT_DIR)),
                }
            )
            manifest["downloaded_count"] += 1
            time.sleep(0.2)

    manifest["filings"].sort(key=lambda f: (f["issuer"], f["fiscal_year"]))
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    if "--discover" in sys.argv:
        discover()
    else:
        result = download_filings()
        print(f"\nTéléchargé {result['downloaded_count']} URD vers {OUTPUT_DIR}")
        print(f"Manifest : {OUTPUT_DIR / 'manifest.json'}")
