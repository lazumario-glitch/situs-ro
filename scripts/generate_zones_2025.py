"""
Generator zone P100-1/2025 (versiunea actualizata 2025) pentru Situs RO.

P100-1/2025 foloseste format nativ diferit fata de P100-2013:
- S_ap,h (m/s2) in loc de ag (g)
- 2 stari limita: SLS (servicovaie) si SLU (ultima)
- Clasificare seismicitate: Mica / Moderata / Mare

Acest script foloseste geometriile aproximate similare cu P100-2013 dar
valorile 2025 atribuite per zona — calibrate pe ~34 capitale jude/orase
majore extrase din Anexa A din PDF oficial AICPS.

Output: data/zone_ag2025_s{N}.geojson, data/zone_tc2025_s{N}.geojson
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
            a, b = pts[i], pts[(i + 1) % n]
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
        clipped = clipped.simplify(SIMPLIFY_TOL[smooth_iters], preserve_topology=True)
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
# P100-2025 — Zone S_ap,h pentru SLU (m/s²)
# Valorile sunt medii din Anexa A pentru fiecare zona aproximata.
# Geometriile sunt similare cu P100-2013 dar valorile reflecta actualizarea
# 2025 (in special pentru zona Vrancea care a crescut cu 0.07-0.16g).
# ============================================================================

# Zonele S_ap,h SLU (concentric Vrancea, valori in m/s²)
# Format: (raw_coords, props with S_SLU + Tc_SLU)

S2025_125 = [(26.85, 45.45), (27.40, 45.40), (27.75, 45.55), (27.85, 45.85),
             (27.60, 46.00), (27.10, 46.00), (26.75, 45.85), (26.70, 45.65)]
# Vrancea core — Focsani: Anexa A spune ~12-15 m/s²

S2025_120 = [(26.30, 44.90), (27.50, 44.85), (28.30, 45.10), (28.50, 45.50),
             (28.40, 45.95), (28.00, 46.20), (27.30, 46.30), (26.40, 46.20),
             (26.05, 45.80), (26.05, 45.40), (26.10, 45.10)]
# Buzau (12.50), Galati (9.41), Braila (9.65)

S2025_110 = [(25.50, 44.10), (28.20, 44.00), (28.30, 44.40), (28.30, 45.30),
             (28.50, 45.80), (28.40, 46.45), (27.50, 46.55), (26.50, 46.30),
             (26.00, 45.85), (25.80, 45.30), (25.50, 44.80)]
# Ploiesti (11.23), Bucuresti (9.09 — borderline), Ialomita

S2025_090 = [(24.00, 43.80), (28.20, 43.70), (28.40, 44.00), (28.50, 44.50),
             (28.55, 45.20), (28.40, 46.20), (28.20, 46.80), (27.80, 47.30),
             (27.00, 47.40), (26.20, 47.20), (25.80, 46.50), (25.80, 45.40),
             (25.10, 45.00), (24.30, 44.80), (24.00, 44.30)]
# Pitesti (7.98), Bacau (10.11 — borderline), Iasi (6.48), Targoviste (10.02)
# Aici merge si Bucuresti daca alegem mai conservator

S2025_065 = [(20.20, 43.65), (29.95, 43.65), (29.95, 44.10), (29.95, 45.50),
             (29.80, 46.50), (29.20, 47.50), (28.20, 48.10), (27.00, 48.20),
             (25.50, 48.05), (23.80, 48.10), (22.00, 48.20), (20.50, 47.50),
             (20.20, 46.50)]
# Brasov (7.47), Constanta (5.46), Suceava (5.0), Sibiu (5.0)
# Olt (5.6), Botosani (5.0), Sfantu Gheorghe (6.88), Slobozia (9.24 — borderline)

S2025_040 = [(22.00, 44.80), (25.00, 44.80), (25.30, 45.50), (25.30, 46.30),
             (25.00, 46.80), (24.30, 47.30), (23.30, 47.95), (22.00, 48.10),
             (21.00, 47.80), (20.80, 47.20), (21.50, 46.50), (22.00, 45.50)]
# Sibiu (5.0), Targu Mures (3.75), Baia Mare (3.75), Oradea (3.75)
# Reșița (5.0), Targu Jiu (3.75)

S2025_030 = [(22.50, 46.30), (24.00, 46.40), (24.40, 46.80), (24.30, 47.20),
             (23.50, 47.30), (22.80, 47.20), (22.50, 46.80)]
# Cluj-Napoca (2.88), Bistrita (2.50), Zalau (2.50)
# Alba Iulia (2.50), Deva (2.50)

# ZONES 2025
ZONES_2025 = {
    "ag2025": {  # Pastram cheia "ag" pentru compatibilitate dar valorile sunt 2025-stil
        "normativ": "P100-1/2025",
        "unit_S": "m/s²",
        "fallback": {"S_SLU": 3.75, "Tc_SLU": 0.8, "seismicitate": "Mică",
                     "label": "S_SLU = 3,75 m/s² (Mică, fallback)"},
        "items": [
            (S2025_125, {"S_SLU": 12.50, "Tc_SLU": 1.8, "seismicitate": "Mare",
                         "label": "S_SLU ≈ 12,5 m/s² (Vrancea, Mare)"}),
            (S2025_120, {"S_SLU": 11.00, "Tc_SLU": 1.8, "seismicitate": "Mare",
                         "label": "S_SLU ≈ 11 m/s² (Mare)"}),
            (S2025_110, {"S_SLU": 10.00, "Tc_SLU": 1.8, "seismicitate": "Mare",
                         "label": "S_SLU ≈ 10 m/s² (Mare)"}),
            (S2025_090, {"S_SLU": 8.50, "Tc_SLU": 1.2, "seismicitate": "Mare",
                         "label": "S_SLU ≈ 8,5 m/s² (Mare)"}),
            (S2025_030, {"S_SLU": 3.00, "Tc_SLU": 0.8, "seismicitate": "Mică",
                         "label": "S_SLU ≈ 3 m/s² (NV/Apuseni, Mică)"}),
            (S2025_040, {"S_SLU": 4.50, "Tc_SLU": 0.8, "seismicitate": "Moderată",
                         "label": "S_SLU ≈ 4,5 m/s² (Moderată)"}),
            (S2025_065, {"S_SLU": 6.50, "Tc_SLU": 0.8, "seismicitate": "Moderată",
                         "label": "S_SLU ≈ 6,5 m/s² (Moderată)"}),
        ],
    },
}

for smooth_level in (0, 1, 2, 3):
    for measurement, cfg in ZONES_2025.items():
        features = []
        for coords, props in cfg["items"]:
            f = build_feature(coords, props, smooth_iters=smooth_level)
            if f:
                features.append(f)
        features.append(build_ro_fallback(cfg["fallback"]))

        out_name = f"zone_{measurement}_s{smooth_level}.geojson"
        with open(os.path.join(OUT_DIR, out_name), "w", encoding="utf-8") as fout:
            json.dump({
                "type": "FeatureCollection",
                "features": features,
                "metadata": {"normativ": cfg["normativ"], "unit": cfg["unit_S"],
                             "smooth": smooth_level},
            }, fout, ensure_ascii=False, separators=(",", ":"))
        size_kb = os.path.getsize(os.path.join(OUT_DIR, out_name)) / 1024
        print(f"  {out_name}: {len(features)} features, {size_kb:.1f} KB")

# Default s2
for measurement in ZONES_2025.keys():
    src = os.path.join(OUT_DIR, f"zone_{measurement}_s2.geojson")
    dst = os.path.join(OUT_DIR, f"zone_{measurement}.geojson")
    with open(src, encoding="utf-8") as fin, open(dst, "w", encoding="utf-8") as fout:
        fout.write(fin.read())

# ============================================================================
# Verificare orase contra valori extrase din PDF oficial
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


# Valori oficiale extrase din Anexa A P100-1/2025
# (lat, lng, S_SLU oficial, Tc_SLU oficial)
ORAS_2025 = [
    ("Focșani",     45.696, 27.186, 12.50, 1.8),  # din Vrancea core (aprox)
    ("Buzău",       45.150, 26.832, 12.50, 1.8),
    ("Ploiești",    44.940, 26.020, 11.23, 1.8),
    ("București",   44.427, 26.103,  9.09, 1.8),
    ("Brașov",      45.660, 25.610,  7.47, 0.8),
    ("Cluj-Napoca", 46.770, 23.590,  2.88, 0.8),
    ("Timișoara",   45.750, 21.230,  5.00, 1.2),
    ("Iași",        47.157, 27.589,  6.48, 0.8),
    ("Constanța",   44.180, 28.650,  5.46, 0.8),
    ("Suceava",     47.640, 26.250,  5.00, 0.8),
    ("Oradea",      47.057, 21.943,  3.75, 0.8),
    ("Craiova",     44.320, 23.800,  5.00, 1.2),
    ("Sibiu",       45.795, 24.150,  5.00, 0.8),
    ("Galați",      45.430, 28.040,  9.41, 1.8),
    ("Baia Mare",   47.660, 23.580,  3.75, 0.8),
    ("Tg. Mureș",   46.542, 24.561,  3.75, 0.8),
    ("Pitești",     44.860, 24.867,  7.98, 1.2),
    ("Bacău",       46.567, 26.914, 10.11, 1.2),
]


def tier_for(s):
    """Bucket aprox pentru S_SLU."""
    if s >= 11: return "high"
    if s >= 9:  return "mid-high"
    if s >= 7:  return "mid"
    if s >= 5:  return "low-mid"
    if s >= 3.5: return "low"
    return "very-low"


print("\n=== Verificare contra valori oficiale P100-1/2025 ===")
print(f"  {'Oraș':14s} {'S_SLU exp':>10s} {'S_SLU got':>10s}  {'tier exp':>10s} {'tier got':>10s}")
ok = 0
for nume, lat, lng, s_exp, tc_exp in ORAS_2025:
    s_got = lookup_in_file(os.path.join(OUT_DIR, "zone_ag2025.geojson"), lng, lat, "S_SLU")
    if s_got is None:
        print(f"  {nume:14s}  (out of zones)")
        continue
    tier_exp = tier_for(s_exp)
    tier_got = tier_for(s_got)
    match = "✓" if tier_exp == tier_got else "✗"
    if tier_exp == tier_got: ok += 1
    print(f"  {nume:14s} {s_exp:>10.2f} {s_got:>10.2f}  {tier_exp:>10s} {tier_got:>10s} {match}")

print(f"\n  Tier match: {ok}/{len(ORAS_2025)} ({100*ok/len(ORAS_2025):.0f}%)")
