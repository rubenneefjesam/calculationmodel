#!/usr/bin/env python3
#
# gen_ranks_v2.py
#
# Genereert top 100 rankings inclusief materiaalkeuzes per scenario.
# Output wordt gebruikt door streamlit_app.py
#
# Gebruik:
#   python scripts/gen_ranks_v2.py
#   python scripts/gen_ranks_v2.py --gebouw gebouw_002 --top 100
#

import argparse
import json
from pathlib import Path

PANEEL_M2_PER_STUK = 1.7

VELD_MAP = {
    "01": ("beglazing_m2",  "m2"),
    "03": ("deuren_stuks",  "stuks"),
    "04": ("gevel_m2",      "m2"),
    "05": ("dak_m2",        "m2"),
    "06": ("kozijnen_m1",   "m1"),
    "07": ("dak_m2",        "stuks"),
    "08": ("dak_m2",        "m2"),
    "09": (None,            "stuks"),
    "10": (None,            "stuks"),
    "11": (None,            "stuks"),
    "12": (None,            "stuks"),
    "13": ("vloer_m2",      "m2"),
    "14": ("dak_m2",        "stuks"),
}


def load_jsonl(path: Path) -> list:
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_gebouw(path: Path, gebouw_id=None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        if gebouw_id:
            for g in data:
                if str(g.get("gebouw_id")) == str(gebouw_id):
                    return g
        return data[0]
    return data


def bereken_optimaal_score(results: list) -> list:
    prijzen = [r["cost_total"] for r in results]
    co2s    = [r["co2_total"]  for r in results]
    p_min, p_max = min(prijzen), max(prijzen)
    c_min, c_max = min(co2s),    max(co2s)
    for r in results:
        p_norm = (r["cost_total"] - p_min) / (p_max - p_min) if p_max != p_min else 0
        c_norm = (r["co2_total"]  - c_min) / (c_max - c_min) if c_max != c_min else 0
        r["optimaal_score"] = round((p_norm + c_norm) / 2, 6)
    return results


def verrijk(scenario: dict, keuzes: dict, mat_lookup: dict, ond_lookup: dict, afm: dict) -> dict:
    """Voeg per-onderdeel detail toe aan een scenario."""
    materialen = []
    for oid, mid in keuzes.items():
        m    = mat_lookup.get(mid, {})
        veld, enh = VELD_MAP.get(oid, (None, ""))

        if veld is None:
            waarde = 1.0
        elif oid in ("07", "14"):
            waarde = round(float(afm.get(veld, 0)) / PANEEL_M2_PER_STUK, 2)
        else:
            waarde = float(afm.get(veld, 0))

        prijs_sub = round(float(m.get("prijs")     or 0) * waarde, 2)
        co2_sub   = round(float(m.get("co2_value") or 0) * waarde, 2)

        materialen.append({
            "onderdeel_id": oid,
            "categorie":    ond_lookup.get(oid, oid),
            "naam":         m.get("naam"),
            "waarde":       waarde,
            "enh":          enh,
            "prijs":        prijs_sub,
            "co2":          co2_sub,
            "duurzaam":     m.get("duurzaam"),
        })

    scenario["materialen"] = materialen
    return scenario


def rank(results: list, key: str, reverse: bool, top_n: int) -> list:
    return sorted(results, key=lambda r: r[key], reverse=reverse)[:top_n]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gebouw",     default=None,                                  help="Gebouw ID")
    parser.add_argument("--results",    default=None,                                  help="Pad naar results_gebouw_xxx.jsonl")
    parser.add_argument("--scenarios",  default="data/output/scenarios.jsonl",          help="Pad naar scenarios.jsonl")
    parser.add_argument("--materials",  default="data/brondata/materials.jsonl",        help="Pad naar materials.jsonl")
    parser.add_argument("--onderdelen", default="data/brondata/onderdelen.jsonl",       help="Pad naar onderdelen.jsonl")
    parser.add_argument("--gebouwdata", default="data/gebouwdata/gebouwgegevens.json",  help="Pad naar gebouwgegevens.json")
    parser.add_argument("--out",        default=None,                                   help="Output pad")
    parser.add_argument("--top",        type=int, default=100,                          help="Top N per ranking (default: 100)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]

    # Bepaal results pad
    if args.results:
        results_path = root / args.results
    elif args.gebouw:
        results_path = root / f"data/output/results_{args.gebouw}.jsonl"
    else:
        matches = list((root / "data/output").glob("results_gebouw_*.jsonl"))
        if not matches:
            print("ERROR: geen results bestand gevonden.")
            return
        results_path = sorted(matches)[0]

    gebouw_id = results_path.stem.replace("results_", "")
    out_path  = root / (args.out or f"data/output/ranks_v2_{gebouw_id}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Laden resultaten...")
    results = load_jsonl(results_path)
    print(f"  {len(results):,} scenario's geladen")

    print(f"Berekenen optimaal scores...")
    results = bereken_optimaal_score(results)

    print(f"Bepalen top {args.top} per ranking...")
    top_goedkoopste = rank(results, "cost_total",     reverse=False, top_n=args.top)
    top_duurste     = rank(results, "cost_total",     reverse=True,  top_n=args.top)
    top_minste_co2  = rank(results, "co2_total",      reverse=False, top_n=args.top)
    top_meeste_co2  = rank(results, "co2_total",      reverse=True,  top_n=args.top)
    top_optimaal    = rank(results, "optimaal_score", reverse=False, top_n=args.top)

    # Unieke scenario IDs die we nodig hebben
    alle_ids = set()
    for lst in [top_goedkoopste, top_duurste, top_minste_co2, top_meeste_co2, top_optimaal]:
        for s in lst:
            alle_ids.add(s["scenario_id"])

    print(f"Laden keuzes voor {len(alle_ids)} unieke scenario's...")
    keuzes_map = {}
    scenarios_path = root / args.scenarios
    with scenarios_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            s = json.loads(line)
            if s["scenario_id"] in alle_ids:
                keuzes_map[s["scenario_id"]] = s["keuzes"]

    print(f"Laden materialen en onderdelen...")
    mat_lookup = {m["material_id"]: m for m in load_jsonl(root / args.materials)}
    ond_lookup = {o["onderdeel_id"]: o["categorie"] for o in load_jsonl(root / args.onderdelen)}
    gebouw     = load_gebouw(root / args.gebouwdata, args.gebouw)
    afm        = gebouw.get("afmetingen", {})

    print(f"Verrijken met materiaalkeuzes...")
    def verrijk_lijst(lst):
        return [verrijk(s.copy(), keuzes_map.get(s["scenario_id"], {}), mat_lookup, ond_lookup, afm) for s in lst]

    output = {
        "gebouw_id":         gebouw_id,
        "totaal_scenarios":  len(results),
        "top_n":             args.top,
        "prijs_min":         min(r["cost_total"] for r in results),
        "prijs_max":         max(r["cost_total"] for r in results),
        "co2_min":           min(r["co2_total"]  for r in results),
        "co2_max":           max(r["co2_total"]  for r in results),
        "top_goedkoopste":   verrijk_lijst(top_goedkoopste),
        "top_duurste":       verrijk_lijst(top_duurste),
        "top_minste_co2":    verrijk_lijst(top_minste_co2),
        "top_meeste_co2":    verrijk_lijst(top_meeste_co2),
        "top_optimaal":      verrijk_lijst(top_optimaal),
    }

    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nOK -> {out_path}")
    print(f"Totaal scenario's: {len(results):,}")
    print(f"Prijs range: €{output['prijs_min']:,.2f} - €{output['prijs_max']:,.2f}")
    print(f"CO2 range:   {output['co2_min']:,.2f} - {output['co2_max']:,.2f}")


if __name__ == "__main__":
    main()