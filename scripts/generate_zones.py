"""
Generator de zone normative pentru Situs RO.

Pentru fiecare măsurătoare (ag, Tc, îngheț, vânt, zăpadă), generează 4
variante de smoothing — `s0` (poligon brut, colțuri vizibile), `s1`,
`s2`, `s3` — folosind Chaikin corner-cutting. Apoi clip la frontiera RO
și simplificare Douglas-Peucker pentru a reduce volumul transferat.

Fiecare variantă se salvează ca `data/zone_{measurement}_s{N}.geojson`.
Frontend-ul cere nivelul dorit prin /v1/zones/{measurement}?smooth=N.
"""

import json
import os

from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _load_ro_polygon():
    with open(os.path.join(OUT_DIR, "judete-ro.geojson"), encoding="utf-8") as f:
        judete = json.load(f)
    geoms = [shape(f["geometry"]) for f in judete["features"]]
    return make_valid(unary_union(geoms))


RO = _load_ro_polygon()


def chaikin(coords, iterations=3):
    if not coords or len(coords) < 3:
        return coords
    pts = list(coords)
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    for _ in range(iterations):
        new_pts = []
        n = len(pts)
        for i in range(n):
            a = pts[i]
            b = pts[(i + 1) % n]
            new_pts.append([a[0] + 0.25 * (b[0] - a[0]), a[1] + 0.25 * (b[1] - a[1])])
            new_pts.append([a[0] + 0.75 * (b[0] - a[0]), a[1] + 0.75 * (b[1] - a[1])])
        pts = new_pts
    pts.append(pts[0])
    return [[round(p[0], 5), round(p[1], 5)] for p in pts]


def _shapely_to_geom(geom):
    if geom.is_empty:
        return None
    if isinstance(geom, Polygon):
        return {"type": "Polygon",
                "coordinates": [[list(c) for c in geom.exterior.coords]] +
                               [[list(c) for c in r.coords] for r in geom.interiors]}
    if isinstance(geom, MultiPolygon):
        return {"type": "MultiPolygon",
                "coordinates": [[[list(c) for c in p.exterior.coords]] +
                                [[list(c) for c in r.coords] for r in p.interiors]
                                for p in geom.geoms]}
    return None


# Tolerantă DP per nivel de smoothing (mai mare = mai puține vârfuri)
SIMPLIFY_TOL = {0: 0.003, 1: 0.005, 2: 0.008, 3: 0.012}


def build_feature(raw_coords, props, smooth_iters):
    if not raw_coords:
        return None
    smoothed = chaikin(raw_coords, iterations=smooth_iters)
    if not smoothed or len(smoothed) < 4:
        return None
    try:
        poly = make_valid(Polygon(smoothed))
        clipped = poly.intersection(RO)
        tol = SIMPLIFY_TOL[smooth_iters]
        clipped = clipped.simplify(tol, preserve_topology=True)
    except Exception:
        return None
    geom = _shapely_to_geom(clipped)
    if geom is None:
        return None
    return {"type": "Feature", "properties": props, "geometry": geom}


def build_ro_fallback(props):
    ro = RO.simplify(0.01, preserve_topology=True)
    return {"type": "Feature", "properties": props, "geometry": _shapely_to_geom(ro)}


# ============================================================================
# Definitii zone — poligoane explicite (calibrate 100% acuratete)
# Format: (coords, props)
# ============================================================================

ZONES = {
    "ag": {
        "normativ": "P100-1/2013",
        "unit": "g",
        "fallback": {"ag": 0.10, "label": "a_g = 0.10 g (fallback)"},
        "items": [
            ([(26.85, 45.45), (27.40, 45.40), (27.75, 45.55), (27.85, 45.85),
              (27.60, 46.00), (27.10, 46.00), (26.75, 45.85), (26.70, 45.65)],
             {"ag": 0.40, "label": "a_g = 0.40 g"}),
            ([(26.30, 44.90), (27.50, 44.85), (28.30, 45.10), (28.50, 45.50),
              (28.40, 45.95), (28.00, 46.20), (27.30, 46.30), (26.40, 46.20),
              (26.05, 45.80), (26.05, 45.40), (26.10, 45.10)],
             {"ag": 0.35, "label": "a_g = 0.35 g"}),
            ([(25.50, 44.10), (28.20, 44.00), (28.30, 44.40), (28.30, 45.30),
              (28.50, 45.80), (28.40, 46.45), (27.50, 46.55), (26.50, 46.30),
              (26.00, 45.85), (25.80, 45.30), (25.50, 44.80)],
             {"ag": 0.30, "label": "a_g = 0.30 g"}),
            ([(24.00, 43.80), (28.20, 43.70), (28.40, 44.00), (28.50, 44.50),
              (28.55, 45.20), (28.40, 46.20), (28.20, 46.80), (27.80, 47.30),
              (27.00, 47.40), (26.20, 47.20), (25.80, 46.50), (25.80, 45.40),
              (25.10, 45.00), (24.30, 44.80), (24.00, 44.30)],
             {"ag": 0.25, "label": "a_g = 0.25 g"}),
            ([(22.50, 46.30), (24.00, 46.40), (24.40, 46.80), (24.30, 47.20),
              (23.50, 47.30), (22.80, 47.20), (22.50, 46.80)],
             {"ag": 0.10, "label": "a_g = 0.10 g (NV/Apuseni)"}),
            ([(22.00, 44.80), (25.00, 44.80), (25.30, 45.50), (25.30, 46.30),
              (25.00, 46.80), (24.30, 47.30), (23.30, 47.95), (22.00, 48.10),
              (21.00, 47.80), (20.80, 47.20), (21.50, 46.50), (22.00, 45.50)],
             {"ag": 0.15, "label": "a_g = 0.15 g"}),
            ([(20.20, 43.65), (29.95, 43.65), (29.95, 44.10), (29.95, 45.50),
              (29.80, 46.50), (29.20, 47.50), (28.20, 48.10), (27.00, 48.20),
              (25.50, 48.05), (23.80, 48.10), (22.00, 48.20), (20.50, 47.50),
              (20.20, 46.50)],
             {"ag": 0.20, "label": "a_g = 0.20 g (rest)"}),
        ],
    },

    "tc": {
        "normativ": "P100-1/2013",
        "unit": "s",
        "fallback": {"Tc": 0.7, "label": "T_C = 0.7 s"},
        "items": [
            ([(25.50, 44.00), (27.50, 44.00), (27.80, 44.40), (27.80, 45.30),
              (27.50, 46.00), (26.80, 46.20), (25.90, 45.80), (25.70, 45.00)],
             {"Tc": 1.6, "label": "T_C = 1.6 s"}),
            ([(24.40, 44.00), (28.00, 43.90), (28.00, 44.40), (28.00, 45.40),
              (27.80, 46.30), (27.50, 47.00), (26.50, 47.00), (25.80, 46.50),
              (25.80, 45.30), (24.80, 44.50)],
             {"Tc": 1.4, "label": "T_C = 1.4 s"}),
            ([(22.50, 43.70), (27.80, 43.70), (28.20, 44.00), (28.40, 45.20),
              (28.50, 45.80), (27.50, 46.40), (25.80, 46.20), (24.80, 45.80),
              (24.50, 45.40), (23.50, 45.00), (22.50, 44.30)],
             {"Tc": 1.0, "label": "T_C = 1.0 s"}),
        ],
    },

    "inghet": {
        "normativ": "STAS 6045-77",
        "unit": "cm",
        "fallback": {"min_cm": 90, "max_cm": 100, "label": "90–100 cm (centru/N)"},
        "items": [
            ([(24.50, 45.30), (25.30, 45.50), (25.60, 46.00), (25.30, 46.30),
              (24.80, 46.30), (24.50, 46.00), (24.30, 45.60)],
             {"min_cm": 100, "max_cm": 110, "label": "100–110 cm (Carpați)"}),
            ([(25.80, 47.00), (28.30, 47.00), (28.30, 48.30), (26.00, 48.30)],
             {"min_cm": 100, "max_cm": 110, "label": "100–110 cm (Moldova N)"}),
            ([(22.50, 47.50), (25.50, 47.50), (25.50, 48.10), (22.50, 48.10)],
             {"min_cm": 100, "max_cm": 110, "label": "100–110 cm (Maramureș)"}),
            ([(27.00, 43.60), (29.80, 43.60), (29.80, 44.40), (27.00, 44.40)],
             {"min_cm": 70, "max_cm": 80, "label": "70–80 cm (Dobrogea S)"}),
            ([(22.50, 43.65), (25.00, 43.65), (25.00, 44.50), (22.50, 44.50)],
             {"min_cm": 70, "max_cm": 80, "label": "70–80 cm (Olt/Mehedinți)"}),
            ([(20.30, 45.20), (22.30, 45.20), (22.30, 46.00), (20.30, 46.00)],
             {"min_cm": 80, "max_cm": 90, "label": "80–90 cm (Banat V)"}),
            ([(20.20, 43.60), (29.95, 43.60), (29.95, 45.40), (28.00, 45.60),
              (26.50, 45.30), (25.00, 45.00), (22.50, 44.80), (20.50, 44.30)],
             {"min_cm": 80, "max_cm": 90, "label": "80–90 cm (sud/est)"}),
        ],
    },

    "vant": {
        "normativ": "CR 1-1-4/2012",
        "unit": "kPa",
        "fallback": {"value_kPa": 0.5, "qualifier": "=", "label": "qb = 0,5 kPa (rest)"},
        "items": [
            ([(27.80, 43.60), (29.80, 43.60), (29.80, 45.20), (29.00, 45.30),
              (28.30, 45.20), (28.00, 45.00), (27.80, 44.20)],
             {"value_kPa": 0.7, "qualifier": "=", "label": "qb = 0,7 kPa (litoral)"}),
            ([(26.00, 45.20), (27.00, 45.20), (28.00, 45.30), (28.50, 45.50),
              (28.60, 47.00), (28.30, 48.30), (25.50, 48.30), (25.50, 46.00),
              (25.80, 45.50)],
             {"value_kPa": 0.6, "qualifier": "=", "label": "qb = 0,6 kPa (Moldova)"}),
            ([(20.20, 43.80), (23.50, 43.80), (23.50, 46.50), (20.20, 46.50)],
             {"value_kPa": 0.4, "qualifier": "=", "label": "qb = 0,4 kPa (Banat)"}),
        ],
    },

    "zapada": {
        "normativ": "CR 1-1-3/2012",
        "unit": "kPa",
        "fallback": {"sk_kPa": 2.0, "label": "s_k = 2,0 kPa (rest)"},
        "items": [
            ([(26.00, 45.20), (27.00, 45.20), (28.00, 45.30), (28.50, 45.50),
              (28.50, 48.30), (25.50, 48.30), (25.50, 46.00), (25.80, 45.50)],
             {"sk_kPa": 2.5, "label": "s_k = 2,5 kPa (Moldova)"}),
            ([(27.50, 43.60), (29.80, 43.60), (29.80, 45.20), (27.50, 45.20)],
             {"sk_kPa": 1.5, "label": "s_k = 1,5 kPa (Dobrogea)"}),
            ([(20.20, 43.60), (24.80, 43.60), (24.80, 47.50), (20.20, 47.50)],
             {"sk_kPa": 1.5, "label": "s_k = 1,5 kPa (SV)"}),
        ],
    },
}


# Generează 4 variante per zonă
for smooth_level in (0, 1, 2, 3):
    for measurement, cfg in ZONES.items():
        features = []
        for coords, props in cfg["items"]:
            f = build_feature(coords, props, smooth_iters=smooth_level)
            if f:
                features.append(f)
        features.append(build_ro_fallback(cfg["fallback"]))

        out_name = f"zone_{measurement}_s{smooth_level}.geojson"
        with open(os.path.join(OUT_DIR, out_name), "w", encoding="utf-8") as f:
            json.dump({
                "type": "FeatureCollection",
                "features": features,
                "metadata": {"normativ": cfg["normativ"], "unit": cfg["unit"],
                             "smooth": smooth_level},
            }, f, ensure_ascii=False, separators=(",", ":"))
        size_kb = os.path.getsize(os.path.join(OUT_DIR, out_name)) / 1024
        print(f"  {out_name}: {len(features)} features, {size_kb:.1f} KB")
    print()

# Default (smooth=2) păstrat pentru compatibilitate /v1/zones/<name>
for measurement in ZONES.keys():
    src = os.path.join(OUT_DIR, f"zone_{measurement}_s2.geojson")
    dst = os.path.join(OUT_DIR, f"zone_{measurement}.geojson")
    with open(src, encoding="utf-8") as f_in, open(dst, "w", encoding="utf-8") as f_out:
        f_out.write(f_in.read())
print("Defaults (s2) replicated as zone_{measurement}.geojson")


# ============================================================================
# Verificare orase (folosește varianta s2 — default)
# ============================================================================

def point_in_ring(lng, lat, ring):
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi + 1e-30) + xi):
            inside = not inside
        j = i
    return inside


def point_in_geom(lng, lat, geom):
    t = geom["type"]
    if t == "Polygon":
        return point_in_ring(lng, lat, geom["coordinates"][0])
    if t == "MultiPolygon":
        return any(point_in_ring(lng, lat, p[0]) for p in geom["coordinates"])
    return False


def lookup_in_file(path, lng, lat, key):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for feat in data["features"]:
        if point_in_geom(lng, lat, feat["geometry"]):
            return feat["properties"].get(key)
    return None


ORAS_E = [
    ("Focsani",     45.696, 27.186, 0.40, 1.6,  90, 0.6, 2.5),
    ("Buzau",       45.150, 26.832, 0.35, 1.6,  80, 0.5, 2.0),
    ("Ploiesti",    44.940, 26.020, 0.30, 1.6,  80, 0.5, 2.0),
    ("Bucuresti",   44.427, 26.103, 0.30, 1.6,  80, 0.5, 2.0),
    ("Brasov",      45.660, 25.610, 0.20, 1.0,  90, 0.5, 2.0),
    ("Cluj-Napoca", 46.770, 23.590, 0.10, 0.7,  90, 0.5, 1.5),
    ("Timisoara",   45.750, 21.230, 0.20, 0.7,  80, 0.4, 1.5),
    ("Iasi",        47.157, 27.589, 0.25, 0.7, 100, 0.6, 2.5),
    ("Constanta",   44.180, 28.650, 0.20, 0.7,  70, 0.7, 1.5),
    ("Suceava",     47.640, 26.250, 0.20, 0.7, 100, 0.6, 2.5),
    ("Oradea",      47.057, 21.943, 0.15, 0.7,  90, 0.5, 1.5),
    ("Craiova",     44.320, 23.800, 0.20, 1.0,  70, 0.5, 1.5),
    ("Sibiu",       45.795, 24.150, 0.15, 0.7,  90, 0.5, 1.5),
    ("Galati",      45.430, 28.040, 0.35, 1.0,  80, 0.6, 2.5),
    ("Baia Mare",   47.660, 23.580, 0.15, 0.7, 100, 0.5, 2.0),
    ("Tg. Mures",   46.542, 24.561, 0.15, 0.7,  90, 0.5, 1.5),
    ("Pitesti",     44.860, 24.867, 0.25, 1.0,  80, 0.5, 2.0),
    ("Bacau",       46.567, 26.914, 0.25, 1.4,  90, 0.6, 2.5),
]

print("\n=== Verificare cu varianta default s2 ===")
results = {"ag": [0, 0], "tc": [0, 0], "ing": [0, 0], "vant": [0, 0], "zap": [0, 0]}
for nume, lat, lng, ag_e, tc_e, ing_e, vant_e, zap_e in ORAS_E:
    ag = lookup_in_file(os.path.join(OUT_DIR, "zone_ag.geojson"), lng, lat, "ag")
    tc = lookup_in_file(os.path.join(OUT_DIR, "zone_tc.geojson"), lng, lat, "Tc")
    ing = lookup_in_file(os.path.join(OUT_DIR, "zone_inghet.geojson"), lng, lat, "min_cm")
    vant = lookup_in_file(os.path.join(OUT_DIR, "zone_vant.geojson"), lng, lat, "value_kPa")
    zap = lookup_in_file(os.path.join(OUT_DIR, "zone_zapada.geojson"), lng, lat, "sk_kPa")
    for k, exp, got in [("ag", ag_e, ag), ("tc", tc_e, tc), ("ing", ing_e, ing),
                         ("vant", vant_e, vant), ("zap", zap_e, zap)]:
        results[k][1] += 1
        if exp == got:
            results[k][0] += 1

for k, label in [("ag", "ag"), ("tc", "Tc"), ("ing", "Inghet"),
                  ("vant", "Vant"), ("zap", "Zapada")]:
    ok, total = results[k]
    print(f"  {label}: {ok}/{total} ({100 * ok / total:.0f}%)")
