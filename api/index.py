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


def _load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


ZONE_AG = _load("zone_ag.geojson")
ZONE_TC = _load("zone_tc.geojson")
ZONE_INGHET = _load("zone_inghet.geojson")
ZONE_VANT = _load("zone_vant.geojson")
ZONE_ZAPADA = _load("zone_zapada.geojson")
JUDETE = _load("judete-ro.geojson")


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


def _point_in_polygon_coords(lng: float, lat: float, polygon_coords) -> bool:
    if not polygon_coords:
        return False
    if not _point_in_ring(lng, lat, polygon_coords[0]):
        return False
    for hole in polygon_coords[1:]:
        if _point_in_ring(lng, lat, hole):
            return False
    return True


def _point_in_geom(lng: float, lat: float, geom) -> bool:
    t = geom.get("type")
    if t == "Polygon":
        return _point_in_polygon_coords(lng, lat, geom["coordinates"])
    if t == "MultiPolygon":
        return any(_point_in_polygon_coords(lng, lat, p) for p in geom["coordinates"])
    return False


def lookup_zone(geojson, lat: float, lng: float):
    for feature in geojson["features"]:
        if _point_in_geom(lng, lat, feature["geometry"]):
            return feature["properties"]
    return None


def find_judet(lat: float, lng: float) -> Optional[str]:
    props = lookup_zone(JUDETE, lat, lng)
    return props["NAME_1"] if props else None


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


def _format_inghet(props) -> dict:
    if props is None:
        return {"min_cm": None, "max_cm": None, "display": "#NA"}
    return {
        "min_cm": props.get("min_cm"),
        "max_cm": props.get("max_cm"),
        "display": props.get("label", f"{props.get('min_cm')}–{props.get('max_cm')} cm"),
    }


def _format_vant(props) -> Optional[dict]:
    if props is None:
        return None
    val = props.get("value_kPa")
    if val is None:
        return None
    qualifier = props.get("qualifier", "=")
    val_str = str(val).replace(".", ",")
    return {
        "value_kPa": val,
        "qualifier": qualifier,
        "display": f"qb {qualifier} {val_str} kPa",
    }


class AdancimeInghet(BaseModel):
    min_cm: Optional[int] = None
    max_cm: Optional[int] = None
    display: str


class PresiuneVant(BaseModel):
    value_kPa: float
    qualifier: str
    display: str


class LookupResponse(BaseModel):
    ag: float
    Tc: float
    adancime_inghet: AdancimeInghet
    presiune_vant: Optional[PresiuneVant]
    incarcare_zapada: Optional[float]
    judet: Optional[str] = Field(None, description="Judetul (informativ).")
    sursa: str
    powered_by: str


app = FastAPI(
    title="Situs RO API",
    summary="Incadrarea tehnica a amplasamentelor din Romania.",
    description=(
        "API REST care determina parametrii normativi de proiectare pentru un punct "
        "geografic din Romania, pe baza standardelor publice:\n\n"
        "- **ag** — acceleratia de proiectare (P100-1/2013)\n"
        "- **Tc** — perioada de colt a spectrului de raspuns (P100-1/2013)\n"
        "- **adancime_inghet** — adancimea maxima de inghet (STAS 6045-77)\n"
        "- **presiune_vant** — presiunea de referinta a vantului (CR 1-1-4/2012)\n"
        "- **incarcare_zapada** — incarcarea caracteristica din zapada in kPa (CR 1-1-3/2012)\n\n"
        "Punctul poate fi specificat prin coordonate (`lat`/`lng`) sau printr-o adresa "
        "in text liber (`address`). Geocodificarea adreselor foloseste "
        "[Photon](https://photon.komoot.io/) cu bias geografic pe Romania.\n\n"
        "Zonarea foloseste poligoane explicite calibrate pe orasele majore din normative."
    ),
    version="2.0.0",
    contact={"name": "Situs RO", "url": "https://github.com/lazumario-glitch/situs-ro"},
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
    responses={422: {"description": "Adresa negasita sau parametri invalizi."}},
)
async def lookup(
    address: Optional[str] = Query(None, examples=["Str. Independentei 1, Iasi"]),
    lat: Optional[float] = Query(None, examples=[44.4268]),
    lng: Optional[float] = Query(None, examples=[26.1025]),
):
    if address and (lat is not None or lng is not None):
        raise HTTPException(422, "Specifica fie `address`, fie `lat`+`lng`, nu ambele.")

    if address:
        coords = geocode_address(address)
        if coords is None:
            raise HTTPException(422, f"Adresa nu a putut fi geocodificata: '{address}'.")
        lat, lng = coords
    elif lat is None or lng is None:
        raise HTTPException(422, "Specifica fie `address`, fie ambele `lat`+`lng`.")

    ag_props = lookup_zone(ZONE_AG, lat, lng)
    tc_props = lookup_zone(ZONE_TC, lat, lng)
    inghet_props = lookup_zone(ZONE_INGHET, lat, lng)
    vant_props = lookup_zone(ZONE_VANT, lat, lng)
    zapada_props = lookup_zone(ZONE_ZAPADA, lat, lng)

    if ag_props is None or tc_props is None:
        raise HTTPException(
            422, f"Amplasamentul ({lat:.4f}, {lng:.4f}) este in afara teritoriului Romaniei."
        )

    return LookupResponse(
        ag=ag_props["ag"],
        Tc=tc_props["Tc"],
        adancime_inghet=AdancimeInghet(**_format_inghet(inghet_props)),
        presiune_vant=PresiuneVant(**_format_vant(vant_props)) if vant_props else None,
        incarcare_zapada=zapada_props.get("sk_kPa") if zapada_props else None,
        judet=find_judet(lat, lng),
        sursa="P100-1/2013, STAS 6045-77, CR 1-1-4/2012, CR 1-1-3/2012",
        powered_by="situs-ro",
    )


@app.get("/v1/zones/{measurement}", summary="GeoJSON pentru o zonare", include_in_schema=True)
async def get_zone_geojson(measurement: str):
    """Returneaza GeoJSON-ul zonarii pentru overlay vizual pe harta."""
    mapping = {
        "ag": ZONE_AG,
        "tc": ZONE_TC,
        "inghet": ZONE_INGHET,
        "vant": ZONE_VANT,
        "zapada": ZONE_ZAPADA,
    }
    if measurement not in mapping:
        raise HTTPException(404, f"Zonare necunoscuta: {measurement}. Disponibile: {list(mapping.keys())}.")
    return mapping[measurement]


if os.path.isdir(PUBLIC_DIR):
    app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")
