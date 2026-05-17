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

Valorile sunt **dominante per județ**, derivate din normativele publice românești (MDLPA). Pentru proiectare oficială, verifică direct în normativele aplicabile — un județ poate cuprinde mai multe zone (în special pentru ag/Tc în județele cu relief variat).

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
