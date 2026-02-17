#!/usr/bin/env python3
#
# compute_results.py
#
# Gebruik:
#   python scripts/compute_results.py --gebouw 1
#

import argparse
import json
from pathlib import Path


TOP_N = 10


# -----------------------------
# Helpers
# -----------------------------

def read_jsonl(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Bestand niet gevonden: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def read_materials_lookup(path: Path):
    lookup = {}

    for m in read_jsonl(path):
        material_id = m.get("material_id")
        if not material_id:
            continue

        lookup[material_id] = {
            "prijs": float(m.get("prijs_norm") or 0),
            "co2": float(m.get("mg_co2_m2") or 0),
            "categorie": m.get("categorie"),
            "enh": (m.get("enh") or "").lower()
        }

    return lookup


def read_gebouw(path: Path, gebouw_id: int):
    for g in read_jsonl(path):
        if g.get("gebouw_id") == gebouw_id:
            return g
    return None


def update_top_list(lst, record, key, reverse=False):
    lst.append(record)
    lst.sort(key=lambda x: x[key], reverse=reverse)
    if len(lst) > TOP_N:
        lst.pop()


def bepaal_factor(materiaal, gebouw):
    categorie = materiaal["categorie"]

    mapping = {
        "Beglazing": "VASTGLAS_m2",
        "Gevelisolatie": "METSELWERK_m2",
        "Plat dakisolatie": "DAKOPPERVLAK_m2",
        "Hellend dakisolatie": "DAKOPPERVLAK_m2",
        "Vloerisolatie": "VLOER_BODEM_m2",
        "Deur": "DEUR_stuks",
        "Kozijnen": "KOZIJNEN_m1"
    }

    veld = mapping.get(categorie)

    if veld and veld in gebouw:
        return float(gebouw.get(veld) or 0)

    # alles zonder oppervlak/stuks → factor = 1
    return 1.0


# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gebouw", type=int, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]

    scenarios_path = root / "data" / "output" / "scenarios.jsonl"
    materials_path = root / "data" / "brondata" / "materials.jsonl"
    gebouw_path = root / "data" / "gebouwdata" / "gebouwgegevens.jsonl"

    output_path = root / "data" / "output" / f"results_summary_gebouw_{args.gebouw}.json"

    print("Laden materialen...")
    material_lookup = read_materials_lookup(materials_path)

    print("Laden gebouw...")
    gebouw = read_gebouw(gebouw_path, args.gebouw)

    if not gebouw:
        print(f"Gebouw {args.gebouw} niet gevonden.")
        return

    goedkoopste = []
    duurste = []
    laagste_co2 = []

    scenario_count = 0

    print("Start berekening...")

    for scenario in read_jsonl(scenarios_path):

        scenario_id = scenario["scenario_id"]
        keuzes = scenario["keuzes"]

        totaal_prijs = 0.0
        totaal_co2 = 0.0

        for material_id in keuzes.values():
            if material_id == "NONE":
                continue

            m = material_lookup.get(material_id)
            if not m:
                continue

            factor = bepaal_factor(m, gebouw)

            totaal_prijs += m["prijs"] * factor
            totaal_co2 += m["co2"] * factor

        record = {
            "scenario_id": scenario_id,
            "totaal_prijs": round(totaal_prijs, 2),
            "totaal_co2": round(totaal_co2, 2)
        }

        update_top_list(goedkoopste, record, "totaal_prijs", reverse=False)
        update_top_list(duurste, record, "totaal_prijs", reverse=True)
        update_top_list(laagste_co2, record, "totaal_co2", reverse=False)

        scenario_count += 1

        # progress feedback elke 25.000 scenario's
        if scenario_count % 25000 == 0:
            print(f"Verwerkt: {scenario_count}")

    result = {
        "meta": {
            "gebouw_id": args.gebouw,
            "scenarios_evaluated": scenario_count
        },
        "goedkoopste_10": goedkoopste,
        "duurste_10": duurste,
        "laagste_co2_10": laagste_co2
    }

    with output_path.open("w", encoding="utf-8") as f_out:
        json.dump(result, f_out, indent=2, ensure_ascii=False)

    print(f"\nOK -> {output_path}")
    print(f"Gebouw: {args.gebouw}")
    print(f"Scenario's geëvalueerd: {scenario_count}")


if __name__ == "__main__":
    main()
