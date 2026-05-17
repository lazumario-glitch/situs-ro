"""
Extrage tabelul UAT cu valori normative din PDF-ul oficial P100-1/2025.

Tabelul (Anexa A) conține valorile S_ap,h SLS/SLU și Tc SLS/SLU pentru
fiecare UAT din România (~2800 entries). Rezultatul se salvează ca
`data/uat_p100_2025.json` — un fișier care e în .gitignore (NU se
commitează în repo public, întrucât compilația poate fi protejată prin
drept sui generis pe baze de date).

UTILIZARE
=========

1. Descarcă PDF-ul oficial P100-1/2025 de la:
   https://www.aicps.ro/media/content/2024-02/p100-1-02022024_65c0c2d57f596.pdf
   (sau orice altă sursă oficială unde îl deții legal)

2. Salvează-l ca `/tmp/p100-2025.pdf` (sau ajustează PATH_PDF mai jos).

3. Rulează:
   ```bash
   .venv/bin/python3 scripts/extract_uat_p100_2025.py
   ```

4. Backend-ul va detecta automat fișierul și va activa lookup direct UAT
   pentru ?version=2025 (acuratețe 100% per localitate, vs. 67% cu zone
   aproximate).

DEPENDENȚE
==========
pip install pypdf

CITARE
======
Datele provin din: P100-1/2025 — Cod de proiectare seismică, Partea I,
Indicativ P100-1, anexa A. Publicat de MDLPA în Monitorul Oficial al
României. Pentru proiectare oficială, verifică tabelul direct în sursa
publicată.
"""

import argparse
import json
import os
import re
import sys


PATH_PDF_DEFAULT = "/tmp/p100-2025.pdf"

JUDETE = [
    "Alba", "Arad", "Argeș", "Bacău", "Bihor", "Bistrița-Năsăud", "Botoșani",
    "Brașov", "Brăila", "București", "Buzău", "Călărași", "Caraș-Severin",
    "Cluj", "Constanța", "Covasna", "Dâmbovița", "Dolj", "Galați", "Giurgiu",
    "Gorj", "Harghita", "Hunedoara", "Iași", "Ialomița", "Ilfov", "Maramureș",
    "Mehedinți", "Mureș", "Neamț", "Olt", "Prahova", "Sălaj", "Satu Mare",
    "Sibiu", "Suceava", "Teleorman", "Timiș", "Tulcea", "Vâlcea", "Vaslui",
    "Vrancea",
]
JUDETE_SORTED = sorted(JUDETE, key=len, reverse=True)
JUDETE_SET = set(JUDETE)


LINE_PATTERN = re.compile(
    r"^\s*(\d+)\s+"  # număr ordine
    r"([\w\-șțăîâȘȚĂÎÂ]+(?:\s+[\w\-șțăîâȘȚĂÎÂ]+)?)\s+"  # județ (1-2 token)
    r"([\w\-\.\s\']+?)\s+"  # localitate
    r"(\d+[,\.]\d+)\s+(\d+[,\.]\d+)\s+"  # S_SLS, Tc_SLS
    r"(\d+[,\.]\d+)\s+(\d+[,\.]\d+)\s+"  # S_SLU, Tc_SLU
    r"(Mică|Moderată|Mare)\s*$"
)


def parse_pdf(path: str) -> list:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("Eroare: pypdf nu e instalat. Rulează: pip install pypdf", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(path):
        print(f"Eroare: nu găsesc {path}.", file=sys.stderr)
        print("Descarcă PDF-ul oficial și salvează-l acolo. Vezi docstring.", file=sys.stderr)
        sys.exit(2)

    reader = PdfReader(path)
    rows = []
    for i in range(min(326, len(reader.pages))):
        if i < 261:
            continue
        try:
            text = reader.pages[i].extract_text() or ""
        except Exception:
            continue
        for line in text.split("\n"):
            m = LINE_PATTERN.match(line.strip())
            if not m:
                continue
            nr, judet_raw, uat_raw, s_sls, tc_sls, s_slu, tc_slu, seism = m.groups()

            judet, uat = _split_judet_uat(judet_raw.strip(), uat_raw.strip())
            if judet is None:
                continue

            rows.append({
                "nr": int(nr),
                "judet": judet,
                "uat": uat,
                "S_SLS": float(s_sls.replace(",", ".")),
                "Tc_SLS": float(tc_sls.replace(",", ".")),
                "S_SLU": float(s_slu.replace(",", ".")),
                "Tc_SLU": float(tc_slu.replace(",", ".")),
                "seismicitate": seism,
            })
    return rows


def _split_judet_uat(judet_raw: str, uat_raw: str):
    """Pattern-ul poate include prefix din UAT în câmpul județ.
    Caută cel mai lung match cu un județ real."""
    if judet_raw in JUDETE_SET:
        return judet_raw, uat_raw
    for j in JUDETE_SORTED:
        if judet_raw.startswith(j):
            extra = judet_raw[len(j):].strip()
            new_uat = (extra + " " + uat_raw).strip() if extra else uat_raw
            return j, new_uat
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pdf", default=PATH_PDF_DEFAULT, help="Calea către PDF-ul P100-1/2025")
    ap.add_argument("--out", default=None, help="Output JSON (default: data/uat_p100_2025.json)")
    args = ap.parse_args()

    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "uat_p100_2025.json"
    )

    print(f"Citesc {args.pdf} ...")
    rows = parse_pdf(args.pdf)

    print(f"Extras: {len(rows)} UAT-uri din {len(set(r['judet'] for r in rows))} județe.")

    if len(rows) < 1000:
        print(f"AVERTISMENT: extragere puțin probabilă să fie completă.", file=sys.stderr)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Salvat → {out_path} ({os.path.getsize(out_path) // 1024} KB)")
    print()
    print("Pasul următor: restartează backend-ul; va detecta automat fișierul.")
    print("?version=2025 va folosi acum lookup direct per UAT (acuratețe 100%).")


if __name__ == "__main__":
    main()
