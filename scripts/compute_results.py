#!/usr/bin/env python3

import argparse
from pathlib import Path

from engine.loader import read_jsonl, read_materials_lookup, read_gebouw
from engine.calculator import bereken_scenario
from engine.ranking import update_top_list
from engine.writer import write_results
from engine.constraints import load_requirements, voldoet_aan_constraints


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gebouw", type=int, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]

    scenarios_path = root / "data" / "output" / "scenarios.jsonl"
    materials_path = root / "data" / "brondata" / "materials.jsonl"
    gebouw_path = root / "data" / "gebouwdata" / "gebouwgegevens.jsonl"
    requirements_path = root / "data" / "config" / "requirements.json"

    output_path = root / "data" / "output" / f"results_summary_gebouw_{args.gebouw}.json"

    print("Laden requirements...")
    requirements = load_requirements(requirements_path)
    constraints = requirements.get("constraints", {})
    objective = requirements.get("objective", {})
    top_n = requirements.get("top_n", 10)

    primary_key = objective.get("primary", "totaal_prijs")
    direction = objective.get("direction", "min")
    reverse = True if direction == "max" else False

    print("Laden materialen...")
    material_lookup = read_materials_lookup(materials_path)

    print("Laden gebouw...")
    gebouw = read_gebouw(gebouw_path, args.gebouw)

    if not gebouw:
        print(f"Gebouw {args.gebouw} niet gevonden.")
        return

    beste_scenarios = []
    scenario_count = 0
    valid_count = 0

    print("Start berekening...")

    for scenario in read_jsonl(scenarios_path):

        scenario_id = scenario["scenario_id"]
        keuzes = scenario["keuzes"]

        totaal_prijs, totaal_co2 = bereken_scenario(
            keuzes, material_lookup, gebouw
        )

        record = {
            "scenario_id": scenario_id,
            "totaal_prijs": totaal_prijs,
            "totaal_co2": totaal_co2
        }

        scenario_count += 1

        # 🔹 Constraints toepassen
        if not voldoet_aan_constraints(record, constraints):
            continue

        valid_count += 1

        # 🔹 Ranking toepassen
        update_top_list(
            beste_scenarios,
            record,
            primary_key,
            reverse,
            top_n
        )

        if scenario_count % 25000 == 0:
            print(f"Verwerkt: {scenario_count}")

    result = {
        "meta": {
            "gebouw_id": args.gebouw,
            "scenarios_evaluated": scenario_count,
            "scenarios_valid": valid_count
        },
        "beste_scenarios": beste_scenarios
    }

    write_results(
        output_path,
        args.gebouw,
        scenario_count,
        beste_scenarios,
        [],
        []
    )

    print(f"\nOK -> {output_path}")
    print(f"Gebouw: {args.gebouw}")
    print(f"Scenario's geëvalueerd: {scenario_count}")
    print(f"Scenario's die voldoen aan requirements: {valid_count}")


if __name__ == "__main__":
    main()