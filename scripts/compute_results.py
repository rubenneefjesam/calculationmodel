#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import argparse
import json

from engine.loader import read_jsonl, read_materials_lookup, read_gebouw
from engine.calculator_totaal_prijs import bereken_totaal_prijs
from engine.calculator_totaal_mg_co2 import bereken_totaal_mg_co2
from engine.ranking import update_top_list
from engine.writer import write_summary
from engine.constraints import load_requirements, voldoet_aan_constraints


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gebouw", type=int, required=True)
    args = parser.parse_args()

    root = ROOT

    scenarios_path    = root / "data" / "output"    / "scenarios.jsonl"
    materials_path    = root / "data" / "brondata"  / "materials.jsonl"
    gebouw_path       = root / "data" / "gebouwdata" / "gebouwgegevens.jsonl"
    requirements_path = root / "data" / "config"    / "requirements.json"

    summary_output_path = root / "data" / "output" / f"results_summary_gebouw_{args.gebouw}.json"
    jsonl_output_path   = root / "data" / "output" / f"scenario_results_gebouw_{args.gebouw}.jsonl"

    jsonl_output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Laden requirements...")
    requirements = load_requirements(requirements_path)
    constraints  = requirements.get("constraints", {})
    objective    = requirements.get("objective", {})
    top_n        = requirements.get("top_n", 10)

    primary_key = objective.get("primary", "totaal_prijs")
    direction   = objective.get("direction", "min")
    reverse     = direction == "max"

    print("Laden materialen...")
    material_lookup = read_materials_lookup(materials_path)

    print("Laden gebouw...")
    gebouw = read_gebouw(gebouw_path, args.gebouw)
    if not gebouw:
        print(f"Gebouw {args.gebouw} niet gevonden.")
        return

    beste_scenarios = []
    scenario_count  = 0
    valid_count     = 0

    print("Start berekening...")

    # ── context manager: één file handle voor alle writes ──────────────────
    with jsonl_output_path.open("w", encoding="utf-8") as f_out:

        for scenario in read_jsonl(scenarios_path):
            scenario_id = scenario["scenario_id"]
            keuzes      = scenario["keuzes"]

            totaal_prijs   = bereken_totaal_prijs(keuzes, material_lookup, gebouw)
            totaal_mg_co2  = bereken_totaal_mg_co2(keuzes, material_lookup, gebouw)

            # Volledige logging naar JSONL
            jsonl_record = {
                "gebouw_id":    args.gebouw,
                "scenario_id":  scenario_id,
                "cost_total":   totaal_prijs,
                "totaal_mg_co2": totaal_mg_co2,
            }
            f_out.write(json.dumps(jsonl_record, ensure_ascii=False) + "\n")

            scenario_count += 1

            # Constraints + ranking
            decision_record = {
                "scenario_id":   scenario_id,
                "totaal_prijs":  totaal_prijs,
                "totaal_mg_co2": totaal_mg_co2,
            }

            if not voldoet_aan_constraints(decision_record, constraints):
                continue

            valid_count += 1

            update_top_list(beste_scenarios, decision_record, primary_key, reverse, top_n)

            if scenario_count % 25000 == 0:
                print(f"Verwerkt: {scenario_count}")

    # ── samenvatting ────────────────────────────────────────────────────────
    result = {
        "meta": {
            "gebouw_id":           args.gebouw,
            "scenarios_evaluated": scenario_count,
            "scenarios_valid":     valid_count,
            "objective":           primary_key,
            "direction":           direction,
            "top_n":               top_n,
        },
        "beste_scenarios": beste_scenarios,
    }

    write_summary(summary_output_path, result)

    print(f"\nOK -> {summary_output_path}")
    print(f"OK -> {jsonl_output_path}")
    print(f"Gebouw:                    {args.gebouw}")
    print(f"Scenario's geëvalueerd:    {scenario_count}")
    print(f"Scenario's valide:         {valid_count}")


if __name__ == "__main__":
    main()