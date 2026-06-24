# /// script
# requires-python = ">=3.12"
# ///
"""Télécharge un échantillon d'URD (Documents d'Enregistrement Universel) du CAC 40
depuis info-financiere.gouv.fr (information réglementée publique de l'AMF).

Source : API Opendatasoft "Explore v2.1" du dataset des flux AMF.
Doc API : https://info-financiere.gouv.fr/pages/api0/

Contrairement à SEC EDGAR (HTML structuré, identifiants CIK), les émetteurs
français sont identifiés par nom/ISIN et les URD sont distribués en PDF.

Le schéma exact des champs du dataset peut évoluer. Lance une fois la découverte
pour vérifier les noms de champs réels avant un téléchargement de masse :

    uv run data/download.py --discover

puis ajuste au besoin les constantes FIELD_* ci-dessous.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib import error, parse, request


# Params : édite-les, puis lance `uv run data/download.py`
USER_AGENT = "Assistant Financier votre.email@example.com"

# Émetteurs CAC 40 : nom affiché -> ISIN.
# La recherche se fait par nom ; l'ISIN sert d'identifiant stable dans le manifest.
ISSUERS = {
    "LVMH": "FR0000121014",
    "TotalEnergies": "FR0000120271",
    "Sanofi": "FR0000120578",
    "L'Oreal": "FR0000120321",
    "Air Liquide": "FR0000120073",
}
DOC_QUERY = "enregistrement universel"  # phrase distinctive identifiant un URD
FILINGS_PER_ISSUER = 5
TARGET_YEARS = {str(year) for year in range(2020, 2026)}
OUTPUT_DIR = Path(__file__).resolve().parent / "downloads"
CLEAR_OUTPUT_DIR = True

API_BASE = "https://www.info-financiere.gouv.fr/api/explore/v2.1"
DATASET = "flux-amf-new-prod"
PAGE_SIZE = 100  # plafond Opendatasoft par page

# Noms de champs du dataset, à confirmer via `--discover`.
# Laissés à None => détection automatique (premier champ plausible).
FIELD_DATE: str | None = None   # champ date de publication (ex. "date_diffusion")
FIELD_TITLE: str | None = None  # champ titre/libellé du document


def get_json(url: str) -> dict:
    req = request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    with request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def get_bytes(url: str) -> bytes:
    req = request.Request(
        url,
        headers={"Accept": "application/pdf,*/*", "User-Agent": USER_AGENT},
    )
    with request.urlopen(req, timeout=120) as response:
        return response.read()


def records_url(where: str, limit: int, offset: int) -> str:
    query = parse.urlencode(
        {"where": where, "limit": limit, "offset": offset, "order_by": "-1"}
    )
    return f"{API_BASE}/catalog/datasets/{DATASET}/records?{query}"


def search_records(where: str, max_records: int) -> list[dict]:
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


def find_year(record: dict) -> str:
    """Extrait une année (YYYY) du champ date configuré, sinon du premier champ
    ressemblant à une date ISO."""
    if FIELD_DATE and isinstance(record.get(FIELD_DATE), str):
        return record[FIELD_DATE][:4]
    for value in record.values():
        if isinstance(value, str) and len(value) >= 4 and value[:4].isdigit():
            year = value[:4]
            if "1900" < year < "2100":
                return year
    return "unknown"


def find_title(record: dict) -> str:
    if FIELD_TITLE and record.get(FIELD_TITLE):
        return str(record[FIELD_TITLE])
    for key in ("titre", "title", "libelle", "objet", "nom"):
        if record.get(key):
            return str(record[key])
    return "document"


def find_pdf_url(record: dict) -> str | None:
    """Détecte l'URL de la pièce jointe sans dépendre d'un nom de champ codé en dur.

    Les champs "fichier" Opendatasoft renvoient soit un dict {url|href|id, ...},
    soit une URL directe en chaîne. On privilégie le PDF."""
    candidates: list[str] = []
    for value in record.values():
        if isinstance(value, dict):
            href = value.get("url") or value.get("href")
            if href:
                candidates.append(href)
            elif value.get("id"):
                candidates.append(
                    f"{API_BASE}/catalog/datasets/{DATASET}/files/{value['id']}"
                )
        elif isinstance(value, str) and value.startswith("http"):
            candidates.append(value)

    if not candidates:
        return None
    pdfs = [c for c in candidates if c.lower().split("?")[0].endswith(".pdf")]
    chosen = (pdfs or candidates)[0]
    return chosen if chosen.startswith("http") else parse.urljoin(API_BASE + "/", chosen)


def discover() -> None:
    """Imprime le schéma du dataset et un enregistrement exemple."""
    meta = get_json(f"{API_BASE}/catalog/datasets/{DATASET}")
    fields = meta.get("dataset", {}).get("fields", meta.get("fields", []))
    print(f"Dataset: {DATASET}\nChamps:")
    for field in fields:
        print(f"  - {field.get('name')} ({field.get('type')}) — {field.get('label')}")
    sample = search_records(f'search("{DOC_QUERY}")', 1)
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
        print(f"Recherche des URD de {name}...")
        where = f'search("{name}") and search("{DOC_QUERY}")'
        records = search_records(where, FILINGS_PER_ISSUER * 4)

        kept = 0
        for record in records:
            if kept >= FILINGS_PER_ISSUER:
                break
            year = find_year(record)
            if year not in TARGET_YEARS:
                continue
            pdf_url = find_pdf_url(record)
            if not pdf_url:
                continue

            slug = "".join(c if c.isalnum() else "-" for c in name.lower())
            year_dir = OUTPUT_DIR / year
            year_dir.mkdir(parents=True, exist_ok=True)
            local_path = year_dir / f"{slug}_urd_{year}_{kept}.pdf"
            try:
                local_path.write_bytes(get_bytes(pdf_url))
            except error.HTTPError as exc:
                print(f"  échec {pdf_url}: {exc}")
                continue

            manifest["filings"].append(
                {
                    "issuer": name,
                    "isin": isin,
                    "document_type": "URD",
                    "year": year,
                    "title": find_title(record),
                    "source_url": pdf_url,
                    "local_path": str(local_path.relative_to(OUTPUT_DIR)),
                }
            )
            manifest["downloaded_count"] += 1
            kept += 1
            time.sleep(0.2)

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    if "--discover" in sys.argv:
        discover()
    else:
        result = download_filings()
        print(f"Téléchargé {result['downloaded_count']} URD vers {OUTPUT_DIR}")
        print(f"Manifest : {OUTPUT_DIR / 'manifest.json'}")
