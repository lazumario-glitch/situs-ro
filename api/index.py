import json
import os
import urllib.parse
import urllib.request
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")


def _load_data():
    with open(os.path.join(DATA_DIR, "judete-ro.geojson"), encoding="utf-8") as f:
        judete = json.load(f)
    with open(os.path.join(DATA_DIR, "normative_per_judet.json"), encoding="utf-8") as f:
        normative = json.load(f)
    return judete, normative["judete"]


JUDETE_GEOJSON, NORMATIVE = _load_data()


def _point_in_ring(lng: float, lat: float, ring) -> bool:
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lng < (xj - xi) * (lat - yi) / (yj - yi + 1e-30) + xi
        ):
            inside = not inside
        j = i
    return inside


def _point_in_polygon(lng: float, lat: float, polygon_coords) -> bool:
    if not polygon_coords:
        return False
    if not _point_in_ring(lng, lat, polygon_coords[0]):
        return False
    for hole in polygon_coords[1:]:
        if _point_in_ring(lng, lat, hole):
            return False
    return True


def _bbox_of_ring(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def find_judet(lat: float, lng: float) -> Optional[str]:
    for feature in JUDETE_GEOJSON["features"]:
        geom = feature["geometry"]
        name = feature["properties"]["NAME_1"]
        polys = (
            [geom["coordinates"]]
            if geom["type"] == "Polygon"
            else geom["coordinates"]
        )
        for poly in polys:
            if not poly:
                continue
            minx, miny, maxx, maxy = _bbox_of_ring(poly[0])
            if not (minx <= lng <= maxx and miny <= lat <= maxy):
                continue
            if _point_in_polygon(lng, lat, poly):
                return name
    return None


def geocode_address(address: str) -> Optional[tuple]:
    params = {
        "q": address,
        "limit": "5",
        "bbox": "20.2,43.6,30.1,48.3",
    }
    url = "https://photon.komoot.io/api?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "situs-ro/1.0 (+https://github.com/lazumario-glitch/situs-ro)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    features = data.get("features", []) if isinstance(data, dict) else []
    for feature in features:
        props = feature.get("properties", {})
        if props.get("countrycode") and props["countrycode"] != "RO":
            continue
        coords = feature.get("geometry", {}).get("coordinates")
        if not coords or len(coords) < 2:
            continue
        try:
            return float(coords[1]), float(coords[0])
        except (ValueError, TypeError):
            continue
    return None


def _format_inghet(min_cm: Optional[int], max_cm: Optional[int]) -> dict:
    if min_cm is None or max_cm is None:
        return {"min_cm": None, "max_cm": None, "display": "#NA"}
    return {
        "min_cm": min_cm,
        "max_cm": max_cm,
        "display": f"{min_cm}–{max_cm} cm",
    }


def _format_vant(value_kPa: Optional[float], qualifier: str) -> Optional[dict]:
    if value_kPa is None:
        return None
    q_display = qualifier if qualifier in ("=", "≥") else "="
    val_str = str(value_kPa).replace(".", ",")
    return {
        "value_kPa": value_kPa,
        "qualifier": q_display,
        "display": f"qb {q_display} {val_str} kPa",
    }


class AdancimeInghet(BaseModel):
    min_cm: Optional[int] = Field(
        None, description="Adancime minima de inghet in centimetri. `null` pentru zona #NA."
    )
    max_cm: Optional[int] = Field(
        None, description="Adancime maxima de inghet in centimetri. `null` pentru zona #NA."
    )
    display: str = Field(..., description="Reprezentare text, ex: `\"80–90 cm\"`.")


class PresiuneVant(BaseModel):
    value_kPa: float = Field(..., description="Presiunea de referinta a vantului in kPa.")
    qualifier: str = Field(..., description="`\"=\"` (valoare exacta) sau `\"≥\"` (valoare minima).")
    display: str = Field(..., description="Reprezentare text, ex: `\"qb = 0,5 kPa\"`.")


class LookupResponse(BaseModel):
    ag: float = Field(..., description="Acceleratia de proiectare in fractiuni de g. P100-1/2013.")
    Tc: float = Field(..., description="Perioada de colt a spectrului de raspuns (s). P100-1/2013.")
    adancime_inghet: AdancimeInghet = Field(..., description="Adancime maxima de inghet. STAS 6045-77.")
    presiune_vant: Optional[PresiuneVant] = Field(None, description="Presiune referinta vant. CR 1-1-4/2012.")
    incarcare_zapada: Optional[float] = Field(None, description="Incarcarea caracteristica din zapada (kPa). CR 1-1-3/2012.")
    judet: str = Field(..., description="Judetul/UAT-ul in care se afla amplasamentul.")
    sursa: str = Field(..., description="Standardele sursa ale datelor.")
    powered_by: str = Field(..., description="Atribuire.")


app = FastAPI(
    title="Situs RO API",
    summary="Incadrarea tehnica a amplasamentelor din Romania.",
    description=(
        "API REST care determina parametrii normativi de proiectare pentru un punct geografic "
        "din Romania, pe baza standardelor publice:\n\n"
        "- **ag** — acceleratia de proiectare ([P100-1/2013](https://www.mdlpa.ro/pages/reglementaritehnice))\n"
        "- **Tc** — perioada de colt a spectrului de raspuns (P100-1/2013)\n"
        "- **adancime_inghet** — adancimea maxima de inghet (STAS 6045-77)\n"
        "- **presiune_vant** — presiunea de referinta a vantului (CR 1-1-4/2012)\n"
        "- **incarcare_zapada** — incarcarea caracteristica din zapada in kPa (CR 1-1-3/2012)\n\n"
        "Punctul poate fi specificat prin coordonate (`lat`/`lng`) sau printr-o adresa in text "
        "liber (`address`). Geocodificarea adreselor foloseste "
        "[Photon](https://photon.komoot.io/) cu bias geografic pe Romania.\n\n"
        "Datele sunt incadrari dominante per judet, derivate din normativele publice."
    ),
    version="1.0.0",
    contact={"name": "Situs RO", "url": "https://github.com/"},
    license_info={"name": "MIT"},
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    index_path = os.path.join(PUBLIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Situs RO API", "docs": "/docs"}


@app.get(
    "/v1/lookup",
    response_model=LookupResponse,
    summary="Incadrarea tehnica a unui amplasament",
    description=(
        "Returneaza incadrarea tehnica (ag, Tc, adancime de inghet, presiune vant, incarcare zapada) "
        "pentru un punct geografic din Romania.\n\n"
        "Specifica fie **coordonate** (`lat` + `lng`), fie o **adresa** in text liber (`address`)."
    ),
    responses={
        422: {"description": "Adresa negasita, amplasament in afara acoperirii, sau parametri invalizi."},
    },
)
async def lookup(
    address: Optional[str] = Query(
        None,
        description="Adresa in text liber, restrictionata la Romania. Ex: `Str. Independentei 1, Iasi`.",
        examples=["Str. Independentei 1, Iasi"],
    ),
    lat: Optional[float] = Query(
        None,
        description="Latitudine WGS84 (EPSG:4326). Obligatorie daca `address` nu e specificat.",
        examples=[44.4268],
    ),
    lng: Optional[float] = Query(
        None,
        description="Longitudine WGS84 (EPSG:4326). Obligatorie daca `address` nu e specificat.",
        examples=[26.1025],
    ),
):
    if address and (lat is not None or lng is not None):
        raise HTTPException(
            status_code=422,
            detail="Specifica fie `address`, fie `lat`+`lng`, nu ambele.",
        )

    if address:
        coords = geocode_address(address)
        if coords is None:
            raise HTTPException(
                status_code=422,
                detail=f"Adresa nu a putut fi geocodificata: '{address}'.",
            )
        lat, lng = coords
    elif lat is None or lng is None:
        raise HTTPException(
            status_code=422,
            detail="Specifica fie `address`, fie ambele `lat`+`lng`.",
        )

    judet = find_judet(lat, lng)
    if judet is None:
        raise HTTPException(
            status_code=422,
            detail=f"Amplasamentul ({lat}, {lng}) este in afara teritoriului Romaniei.",
        )

    norm = NORMATIVE.get(judet)
    if norm is None:
        raise HTTPException(
            status_code=422,
            detail=f"Nu exista date normative pentru '{judet}'.",
        )

    return LookupResponse(
        ag=norm["ag"],
        Tc=norm["Tc"],
        adancime_inghet=AdancimeInghet(**_format_inghet(norm["inghet_min"], norm["inghet_max"])),
        presiune_vant=(
            PresiuneVant(**_format_vant(norm["vant"], norm["vant_qual"]))
            if norm.get("vant") is not None
            else None
        ),
        incarcare_zapada=norm.get("zapada"),
        judet=judet,
        sursa="P100-1/2013, STAS 6045-77, CR 1-1-4/2012, CR 1-1-3/2012",
        powered_by="situs-ro",
    )


@app.get("/v1/judete", summary="Lista judetelor cu valorile normative", include_in_schema=True)
async def list_judete():
    return {"judete": NORMATIVE}


if os.path.isdir(PUBLIC_DIR):
    app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")
