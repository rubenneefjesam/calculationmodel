#!/usr/bin/env python3
#
# gen_results.py
#
# Berekent prijs + CO2 per scenario en schrijft naar JSONL.
#
# Gebruik:
#   python scripts/gen_results.py
#   python scripts/gen_results.py --gebouw gebouw_002
#

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.loader     import read_jsonl, read_materials_lookup, read_gebouw
from engine.calculator import bereken_totaal_prijs, bereken_totaal_co2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gebouw",      default=None,                                  help="Gebouw ID")
    parser.add_argument("--scenarios",   default="data/output/scenarios.jsonl",          help="Pad naar scenarios.jsonl")
    parser.add_argument("--materials",   default="data/brondata/materials.jsonl",        help="Pad naar materials.jsonl")
    parser.add_argument("--gebouwdata",  default="data/gebouwdata/gebouwgegevens.json",  help="Pad naar gebouwgegevens.json")
    parser.add_argument("--out",         default=None,                                   help="Output pad (default: data/output/results_gebouw_<id>.jsonl)")
    args = parser.parse_args()

    root = ROOT

    gebouw = read_gebouw(root / args.gebouwdata, args.gebouw)
    if not gebouw:
        print("ERROR: gebouw niet gevonden.")
        return

    gebouw_id = gebouw.get("gebouw_id", "onbekend")
    out_path  = root / (args.out or f"data/output/results_{gebouw_id}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Gebouw:    {gebouw_id}")
    print(f"Laden materialen...")
    material_lookup = read_materials_lookup(root / args.materials)
    print(f"  {len(material_lookup)} materialen geladen")

    print(f"Start berekening...")

    count = 0
    with out_path.open("w", encoding="utf-8") as f_out:
        for scenario in read_jsonl(root / args.scenarios):
            keuzes = scenario["keuzes"]

            prijs = bereken_totaal_prijs(keuzes, material_lookup, gebouw)
            co2   = bereken_totaal_co2(keuzes, material_lookup, gebouw)

            record = {
                "gebouw_id":   gebouw_id,
                "scenario_id": scenario["scenario_id"],
                "cost_total":  prijs,
                "co2_total":   co2,
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

            count += 1
            if count % 25000 == 0:
                print(f"  Verwerkt: {count:,}")

    print(f"\nOK -> {out_path}")
    print(f"Scenario's berekend: {count:,}")


if __name__ == "__main__":
    main()