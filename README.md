# Situs RO

API + interfață web pentru determinarea parametrilor normativi de proiectare pentru orice punct din România:

- **a<sub>g</sub>** — accelerația de proiectare (P100-1/2013)
- **T<sub>C</sub>** — perioada de colț a spectrului de răspuns (P100-1/2013)
- **adâncime îngheț** — adâncimea maximă de îngheț (STAS 6045-77)
- **presiune vânt** — presiunea de referință a vântului (CR 1-1-4/2012)
- **încărcare zăpadă** — încărcarea caracteristică din zăpadă (CR 1-1-3/2012)

## Cum folosești API-ul

### Prin coordonate

```bash
curl "https://<domeniu>/v1/lookup?lat=44.4268&lng=26.1025"
```

### Prin adresă

```bash
curl "https://<domeniu>/v1/lookup?address=Str.%20Independentei%201,%20Iasi"
```

### Răspuns

```json
{
  "ag": 0.30,
  "Tc": 1.6,
  "adancime_inghet": { "min_cm": 80, "max_cm": 90, "display": "80–90 cm" },
  "presiune_vant":   { "value_kPa": 0.5, "qualifier": "=", "display": "qb = 0,5 kPa" },
  "incarcare_zapada": 2.0,
  "judet": "Bucuresti",
  "sursa": "P100-1/2013, STAS 6045-77, CR 1-1-4/2012, CR 1-1-3/2012",
  "powered_by": "situs-ro"
}
```

## Documentație interactivă

`/docs` — Swagger UI auto-generat de FastAPI.

## Surse de date

Valorile sunt **aproximate din hărțile normativelor publice românești** (MDLPA), folosind poligoane explicite calibrate să dea răspunsurile corecte pe **18 orașe-reper** (Focșani, Buzău, Ploiești, București, Brașov, Cluj-Napoca, Timișoara, Iași, Constanța, Suceava, Oradea, Craiova, Sibiu, Galați, Baia Mare, Tg. Mureș, Pitești, Bacău). Pentru proiectare oficială, verifică direct anexele normativelor sau [harta interactivă MDLPA](https://observator.mdlpa.ro/portal/apps/webappviewer/index.html?id=ceab6fd501124bcaaa701a8e2baf6a36).

## Limitări

- **P100-1/2013 vs P100-1/2025**: site-ul folosește valori conforme **P100-1/2013** by default (cu toggle pentru P100-1/2025). Normativul **P100-1/2025** are valori actualizate (în special pentru zona Vrancea) și format diferit (`S_ap,h` în m/s², cu 2 stări limită SLS/SLU).
- **P100-2013 nu are tabel UAT oficial** — doar hărți. Valorile sunt extrase de specialiști din hărți și pot varia ±0.05g între surse pentru orașele la limita între zone.
- Coordonate prin geocodare Photon (OSM) — acuratețe ~50m pentru orașe, mai variabilă pentru adrese rurale.
- Zonele sunt mărginite la perimetrul administrativ al României.

## Mod "full P100-2025" (lookup direct per UAT)

Default, varianta **P100-2025** din interfață folosește **zone aproximate** (acuratețe ~67% per tier de seismicitate). Pentru **acuratețe 100% per UAT**, există un mod opțional care folosește tabelul oficial Anexa A din PDF-ul P100-1/2025:

### Activare (local)

1. Descarcă PDF-ul oficial P100-1/2025 de la o sursă unde îl deții legal (ex: [AICPS](https://www.aicps.ro/)) și salvează-l ca `/tmp/p100-2025.pdf`.
2. Generează tabelul UAT local:
   ```bash
   .venv/bin/pip install pypdf
   .venv/bin/python3 scripts/extract_uat_p100_2025.py
   ```
3. Restartează backend. Vei vedea în log: `P100-2025 UAT table loaded: ~2800 entries`.
4. Pentru orice coordonată, răspunsul include acum câmpul `p100_2025` cu label `(exact, Anexa A)` în loc de `(aproximat)`.

### De ce nu e în repo public?

Tabelul cu ~2800 UAT-uri + valorile lor reprezintă o **compilație substanțială** din actul normativ oficial. Standardul în sine e act normativ (textul nu e protejat de copyright per Legea 8/1996 art. 9), dar compilația poate intra sub regimul de **drept sui generis pe baze de date** (Directiva UE 96/9/EC). Pentru a evita orice ambiguitate, fișierul `data/uat_p100_2025.json` e listat în `.gitignore`. Fiecare utilizator îl regenerează local din propria copie a PDF-ului oficial.

### Comportament pe deploy public

Pe deploy-ul Vercel (situs-ro.vercel.app), tabelul **nu** e prezent → fallback automat la zone aproximate. Toate funcționalitățile rămân operaționale, doar acuratețea P100-2025 e ~67% în loc de 100%.

| Normativ | Sursă oficială |
|---|---|
| P100-1/2013 | [mdlpa.ro](https://www.mdlpa.ro/pages/reglementaritehnice) |
| STAS 6045-77 | Standard de stat |
| CR 1-1-3/2012 | MDLPA |
| CR 1-1-4/2012 | MDLPA |

## Stack

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: HTML + Leaflet (carto basemap)
- **Geocodare**: Photon (komoot.io, OSM open-source)
- **Date**: GeoJSON (limite administrative) + JSON lookup per județ
- **Deploy**: Vercel (serverless functions Python + static)

## Dezvoltare locală

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install uvicorn
uvicorn api.index:app --reload --port 8000
```

Apoi accesează:
- `http://localhost:8000/` — UI
- `http://localhost:8000/docs` — Swagger
- `http://localhost:8000/v1/lookup?lat=44.4268&lng=26.1025` — test endpoint

## Deploy

Push la `main` declanșează auto-deploy pe Vercel.

## Licență

MIT.
