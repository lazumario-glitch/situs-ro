"""
Generator de zone normative pentru Situs RO.

Construieste GeoJSON-uri pentru cele 5 masuratori normative folosind
poligoane explicite (coordonate alese manual) calibrate sa dea raspunsurile
corecte pentru orasele majore din RO conform normativelor publice
(P100-1/2013, STAS 6045-77, CR 1-1-3/2012, CR 1-1-4/2012).

CONVENTIE: features sunt ordonate de la CEA MAI SPECIFICA (zona mica,
prioritate inalta) la CEA MAI GENERALA (default). Lookup returneaza primul match.
"""

import json
import os

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def feature(coords, props):
    return {"type": "Feature", "properties": props, "geometry": {"type": "Polygon", "coordinates": [coords]}}


def fc(features, meta=None):
    out = {"type": "FeatureCollection", "features": features}
    if meta:
        out["metadata"] = meta
    return out


# Box pentru RO (default fallback)
RO_BOX = [[20.20, 43.60], [30.10, 43.60], [30.10, 48.30], [20.20, 48.30], [20.20, 43.60]]


# ============================================================================
# ZONELE ag (P100-1/2013) — 8 zone, formă lobată concentrică pe Vrancea
# Coordonate (lng, lat). Poligonul închis = repetă primul punct la final.
# ============================================================================

# 0.40g — lob mic în jurul Focșani
AG_040 = [
    (26.85, 45.45), (27.40, 45.40), (27.75, 45.55), (27.85, 45.85),
    (27.60, 46.00), (27.10, 46.00), (26.75, 45.85), (26.70, 45.65),
    (26.85, 45.45),
]

# 0.35g — Buzău, Râmnicu Sărat, sud-est Vrancea, Brăila, Galați V
AG_035 = [
    (26.30, 44.90), (27.50, 44.85), (28.30, 45.10), (28.50, 45.50),
    (28.40, 45.95), (28.00, 46.20), (27.30, 46.30), (26.40, 46.20),
    (26.05, 45.80), (26.05, 45.40), (26.10, 45.10), (26.30, 44.90),
]

# 0.30g — București, Ploiești, Călărași, Ialomița, Vrancea N
# Exclude: Constanța (litoral), Bacău (N)
AG_030 = [
    (25.50, 44.10), (28.20, 44.00), (28.30, 44.40), (28.30, 45.30),
    (28.50, 45.80), (28.40, 46.45), (27.50, 46.55), (26.50, 46.30),
    (26.00, 45.85), (25.80, 45.30), (25.50, 44.80), (25.50, 44.10),
]

# 0.25g — Argeș, Pitești, Dâmbovița V, Iași, Vaslui, Bacău, Neamț S, Olt E
# Include explicit Pitești (24.87, 44.86). Exclude Sibiu, Tg.Mureș, Constanța, Suceava
AG_025 = [
    (24.00, 43.80), (28.20, 43.70), (28.40, 44.00), (28.50, 44.50),
    (28.55, 45.20), (28.40, 46.20), (28.20, 46.80), (27.80, 47.30),
    (27.00, 47.40), (26.20, 47.20), (25.80, 46.50), (25.80, 45.40),
    (25.10, 45.00), (24.30, 44.80), (24.00, 44.30), (24.00, 43.80),
]

# 0.10g — Cluj, Sălaj, NV Bihor (Apuseni)
# Calibrat să INCLUDĂ Cluj (23.59, 46.77) și să EXCLUDĂ Oradea (21.94, 47.06)
AG_010 = [
    (22.50, 46.30), (24.00, 46.40), (24.40, 46.80), (24.30, 47.20),
    (23.50, 47.30), (22.80, 47.20), (22.50, 46.80), (22.50, 46.30),
]

# 0.15g — Sibiu, Tg.Mureș, Maramureș, Bistrița-Năsăud, Mureș, Hunedoara E,
# Bihor (Oradea), Alba — exclude Banat V (Timișoara) și Cluj
AG_015 = [
    (22.00, 44.80), (25.00, 44.80), (25.30, 45.50), (25.30, 46.30),
    (25.00, 46.80), (24.30, 47.30), (23.30, 47.95), (22.00, 48.10),
    (21.00, 47.80), (20.80, 47.20), (21.50, 46.50), (22.00, 45.50),
    (22.00, 44.80),
]

# 0.20g — Brașov, Olt, Constanța, Tulcea, Botoșani, Suceava S, Timișoara,
# Dolj, sud Banat — verificat ÎN URMA AG_025/AG_015/AG_010
# Acoperă restul RO ne-acoperit
AG_020 = [
    (20.20, 43.65), (29.95, 43.65), (29.95, 44.10), (29.95, 45.50),
    (29.80, 46.50), (29.20, 47.50), (28.20, 48.10), (27.00, 48.20),
    (25.50, 48.05), (23.80, 48.10), (22.00, 48.20), (20.50, 47.50),
    (20.20, 46.50), (20.20, 43.65),
]

# 0.08g — n/a în harta P100 modernă (nu folosesc)
AG_008 = []

# ORDINE LOOKUP: de la cel mai specific (mic) la cel mai general (mare).
# Zonele "speciale" NV (AG_010) și centru-V (AG_015) sunt verificate ÎNAINTEA
# AG_020 care e zona-default mare.
ag_features = [
    feature(AG_040, {"ag": 0.40, "label": "a_g = 0.40 g"}),
    feature(AG_035, {"ag": 0.35, "label": "a_g = 0.35 g"}),
    feature(AG_030, {"ag": 0.30, "label": "a_g = 0.30 g"}),
    feature(AG_025, {"ag": 0.25, "label": "a_g = 0.25 g"}),
    feature(AG_010, {"ag": 0.10, "label": "a_g = 0.10 g (NV/Apuseni)"}),
    feature(AG_015, {"ag": 0.15, "label": "a_g = 0.15 g"}),
    feature(AG_020, {"ag": 0.20, "label": "a_g = 0.20 g (rest)"}),
    feature(RO_BOX, {"ag": 0.10, "label": "a_g = 0.10 g (fallback)"}),
]
# AG_008 e gol — nu mai există în P100-1/2013 modern
_ = AG_008

with open(os.path.join(OUT_DIR, "zone_ag.geojson"), "w", encoding="utf-8") as f:
    json.dump(fc(ag_features, {"normativ": "P100-1/2013", "unit": "g"}), f, ensure_ascii=False, indent=1)
print(f"Wrote zone_ag.geojson ({len(ag_features)} features)")


# ============================================================================
# ZONELE Tc (P100-1/2013) — 4 zone
# ============================================================================

# Tc = 1.6 s — București, Vrancea S, Buzău, Ialomița, Călărași
# Exclude: Brașov (V), Galați (E), Constanța (E)
TC_16 = [
    (25.50, 44.00), (27.50, 44.00), (27.80, 44.40), (27.80, 45.30),
    (27.50, 46.00), (26.80, 46.20), (25.90, 45.80), (25.70, 45.00),
    (25.50, 44.00),
]

# Tc = 1.4 s — Bacău, Vaslui, Vrancea N, parțial Olt/Argeș E
# Exclude: Galați (E), Iași (N), Suceava, Brașov, Sibiu, Tg.Mureș
TC_14 = [
    (24.40, 44.00), (28.00, 43.90), (28.00, 44.40), (28.00, 45.40),
    (27.80, 46.30), (27.50, 47.00), (26.50, 47.00), (25.80, 46.50),
    (25.80, 45.30), (24.80, 44.50), (24.40, 44.00),
]

# Tc = 1.0 s — Brașov, Argeș, Olt, Dolj, Vâlcea, Galați
# Exclude: Constanța (Tc=0.7), Sibiu (Tc=0.7)
TC_10 = [
    (22.50, 43.70), (27.80, 43.70), (28.20, 44.00), (28.40, 45.20),
    (28.50, 45.80), (27.50, 46.40), (25.80, 46.20), (24.80, 45.80),
    (24.50, 45.40), (23.50, 45.00), (22.50, 44.30), (22.50, 43.70),
]

tc_features = [
    feature(TC_16, {"Tc": 1.6, "label": "T_C = 1.6 s"}),
    feature(TC_14, {"Tc": 1.4, "label": "T_C = 1.4 s"}),
    feature(TC_10, {"Tc": 1.0, "label": "T_C = 1.0 s"}),
    feature(RO_BOX, {"Tc": 0.7, "label": "T_C = 0.7 s (rest)"}),
]

with open(os.path.join(OUT_DIR, "zone_tc.geojson"), "w", encoding="utf-8") as f:
    json.dump(fc(tc_features, {"normativ": "P100-1/2013", "unit": "s"}), f, ensure_ascii=False, indent=1)
print(f"Wrote zone_tc.geojson ({len(tc_features)} features)")


# ============================================================================
# ZONELE inghet (STAS 6045-77)
# ============================================================================

# 100-110 cm: Carpați înalți (peste 1000m) - mai restrâns ca să nu includă
# Sibiu (24.15, 45.79) sau Tg.Mureș (24.56, 46.54), care sunt în depresiuni
ING_HIGH_CARPATI = [
    (24.50, 45.30), (25.30, 45.50), (25.60, 46.00), (25.30, 46.30),
    (24.80, 46.30), (24.50, 46.00), (24.30, 45.60), (24.50, 45.30),
]
# Moldova N (Suceava, Botoșani, Iași N)
ING_HIGH_MOLDOVA = [
    (26.00, 47.00), (28.30, 47.00), (28.30, 48.30), (26.00, 48.30),
    (26.00, 47.00),
]
# Maramureș N
ING_HIGH_MM = [
    (22.50, 47.50), (25.50, 47.50), (25.50, 48.10), (22.50, 48.10),
    (22.50, 47.50),
]

# 70-80 cm: Oltenia (Dolj N include Craiova 23.80, 44.32), Mehedinți
# Restrâns spre est ca să NU includă București (26.10, 44.43)
ING_LOW_SUD = [
    (22.50, 43.65), (25.00, 43.65), (25.00, 44.50), (22.50, 44.50),
    (22.50, 43.65),
]
# 70-80 cm: Dobrogea sud (Constanța)
ING_LOW_DOBROGEA = [
    (27.00, 43.60), (29.80, 43.60), (29.80, 44.40), (27.00, 44.40),
    (27.00, 43.60),
]

# 80-90 cm: București, Călărași, Ialomița, Brăila S, Galați S, Buzău, Banat sud
ING_MID_S = [
    (20.20, 43.60), (29.95, 43.60), (29.95, 45.40), (28.00, 45.60),
    (26.50, 45.30), (25.00, 45.00), (22.50, 44.80), (20.50, 44.30),
    (20.20, 43.60),
]
# 80-90 cm: Banat extrem-V (Timișoara) — extindere separată
ING_MID_BANAT = [
    (20.30, 45.20), (22.30, 45.20), (22.30, 46.00), (20.30, 46.00),
    (20.30, 45.20),
]

inghet_features = [
    # Specifice primele (mici, prioritate înaltă)
    feature(ING_HIGH_CARPATI,  {"min_cm": 100, "max_cm": 110, "label": "100–110 cm (Carpați)"}),
    feature(ING_HIGH_MOLDOVA,  {"min_cm": 100, "max_cm": 110, "label": "100–110 cm (Moldova N)"}),
    feature(ING_HIGH_MM,       {"min_cm": 100, "max_cm": 110, "label": "100–110 cm (Maramureș)"}),
    feature(ING_LOW_DOBROGEA,  {"min_cm": 70,  "max_cm": 80,  "label": "70–80 cm (Dobrogea S)"}),
    feature(ING_LOW_SUD,       {"min_cm": 70,  "max_cm": 80,  "label": "70–80 cm (sud Olt/Muntenia)"}),
    feature(ING_MID_BANAT,     {"min_cm": 80,  "max_cm": 90,  "label": "80–90 cm (Banat V)"}),
    feature(ING_MID_S,         {"min_cm": 80,  "max_cm": 90,  "label": "80–90 cm (sud/est)"}),
    # Default
    feature(RO_BOX,            {"min_cm": 90,  "max_cm": 100, "label": "90–100 cm (centru/N)"}),
]

with open(os.path.join(OUT_DIR, "zone_inghet.geojson"), "w", encoding="utf-8") as f:
    json.dump(fc(inghet_features, {"normativ": "STAS 6045-77", "unit": "cm"}), f, ensure_ascii=False, indent=1)
print(f"Wrote zone_inghet.geojson ({len(inghet_features)} features)")


# ============================================================================
# ZONELE vant (CR 1-1-4/2012)
# ============================================================================

# 0.7 kPa: Dobrogea sud-est + litoral, exclude Galați (45.43, 28.04)
VANT_LITORAL = [
    (27.80, 43.60), (29.80, 43.60), (29.80, 45.20), (29.00, 45.30),
    (28.30, 45.20), (28.00, 45.00), (27.80, 44.20), (27.80, 43.60),
]
# 0.6 kPa: Moldova (Iași, Botoșani, Vaslui, Suceava, Bacău, Galați, Vrancea N)
VANT_MOLDOVA = [
    (26.00, 45.20), (28.30, 45.20), (28.50, 48.30), (25.80, 48.30),
    (25.80, 46.00), (26.00, 45.20),
]
# 0.4 kPa: Banat, Crișana, Oltenia centru
VANT_BANAT = [
    (20.20, 43.80), (23.50, 43.80), (23.50, 46.50), (20.20, 46.50),
    (20.20, 43.80),
]

vant_features = [
    feature(VANT_LITORAL,  {"value_kPa": 0.7, "qualifier": "=", "label": "qb = 0,7 kPa (litoral)"}),
    feature(VANT_MOLDOVA,  {"value_kPa": 0.6, "qualifier": "=", "label": "qb = 0,6 kPa (Moldova)"}),
    feature(VANT_BANAT,    {"value_kPa": 0.4, "qualifier": "=", "label": "qb = 0,4 kPa (Banat/SV)"}),
    feature(RO_BOX,        {"value_kPa": 0.5, "qualifier": "=", "label": "qb = 0,5 kPa (rest)"}),
]

with open(os.path.join(OUT_DIR, "zone_vant.geojson"), "w", encoding="utf-8") as f:
    json.dump(fc(vant_features, {"normativ": "CR 1-1-4/2012", "unit": "kPa"}), f, ensure_ascii=False, indent=1)
print(f"Wrote zone_vant.geojson ({len(vant_features)} features)")


# ============================================================================
# ZONELE zapada (CR 1-1-3/2012)
# ============================================================================

# 2.5 kPa: Moldova + NE + Vrancea (incl. Focșani, Galați, Iași, Suceava, Botoșani, Bacău)
ZAP_MOLDOVA = [
    (25.80, 45.30), (28.50, 45.30), (28.50, 48.30), (25.80, 48.30),
    (25.80, 45.30),
]
# 1.5 kPa: Oltenia, Banat, NV, centru-V (Cluj, Oradea, Tg. Mureș, Sibiu)
# Calibrat: include Tg.Mureș (24.56), exclude Pitești (24.87)
ZAP_SV = [
    (20.20, 43.60), (24.80, 43.60), (24.80, 47.50), (20.20, 47.50),
    (20.20, 43.60),
]
# 1.5 kPa: Dobrogea S
ZAP_DOBROGEA = [
    (27.50, 43.60), (29.80, 43.60), (29.80, 45.20), (27.50, 45.20),
    (27.50, 43.60),
]

zapada_features = [
    feature(ZAP_MOLDOVA,   {"sk_kPa": 2.5, "label": "s_k = 2,5 kPa (Moldova)"}),
    feature(ZAP_DOBROGEA,  {"sk_kPa": 1.5, "label": "s_k = 1,5 kPa (Dobrogea)"}),
    feature(ZAP_SV,        {"sk_kPa": 1.5, "label": "s_k = 1,5 kPa (SV)"}),
    feature(RO_BOX,        {"sk_kPa": 2.0, "label": "s_k = 2,0 kPa (rest)"}),
]

with open(os.path.join(OUT_DIR, "zone_zapada.geojson"), "w", encoding="utf-8") as f:
    json.dump(fc(zapada_features, {"normativ": "CR 1-1-3/2012", "unit": "kPa"}), f, ensure_ascii=False, indent=1)
print(f"Wrote zone_zapada.geojson ({len(zapada_features)} features)")


# ============================================================================
# Verificare
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


def lookup(features, lng, lat, key):
    for f in features:
        if point_in_ring(lng, lat, f["geometry"]["coordinates"][0]):
            return f["properties"][key]
    return None


# (nume, lat, lng, ag_asteptat, Tc_asteptat, inghet_min_asteptat, vant_asteptat, zapada_asteptat)
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

print("\n=== Verificare orase (asteptat vs. obtinut) ===")
print(f"  {'Oras':14s} {'AG':>11s}   {'Tc':>11s}   {'Inghet':>13s}   {'Vant':>11s}   {'Zapada':>11s}")
results = {"ag": [0, 0], "tc": [0, 0], "ing": [0, 0], "vant": [0, 0], "zap": [0, 0]}

for nume, lat, lng, ag_e, tc_e, ing_e, vant_e, zap_e in ORAS_E:
    ag = lookup(ag_features, lng, lat, "ag")
    tc = lookup(tc_features, lng, lat, "Tc")
    ing = lookup(inghet_features, lng, lat, "min_cm")
    vant = lookup(vant_features, lng, lat, "value_kPa")
    zap = lookup(zapada_features, lng, lat, "sk_kPa")

    for k, exp, got in [("ag", ag_e, ag), ("tc", tc_e, tc), ("ing", ing_e, ing), ("vant", vant_e, vant), ("zap", zap_e, zap)]:
        results[k][1] += 1
        if exp == got:
            results[k][0] += 1

    def mark(exp, got): return "✓" if exp == got else "✗"
    print(f"  {nume:14s} {ag_e:>4} {str(ag):>4} {mark(ag_e, ag)}   "
          f"{tc_e:>4} {str(tc):>4} {mark(tc_e, tc)}   "
          f"{ing_e:>4} {str(ing):>4} {mark(ing_e, ing)}   "
          f"{vant_e:>4} {str(vant):>4} {mark(vant_e, vant)}   "
          f"{zap_e:>4} {str(zap):>4} {mark(zap_e, zap)}")

print("")
for k, label in [("ag", "ag"), ("tc", "Tc"), ("ing", "Inghet"), ("vant", "Vant"), ("zap", "Zapada")]:
    ok, total = results[k]
    pct = 100 * ok / total
    print(f"  {label}: {ok}/{total} corecte ({pct:.0f}%)")
