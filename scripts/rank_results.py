#!/usr/bin/env python3
# scripts/rank_results.py

import argparse
import json
from pathlib import Path

INF = float("inf")


def read_jsonl(path: Path):
    if not path.exists():
        raise SystemExit(f"Results file niet gevonden: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def to_float(value, default=INF):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def show(title, items):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(f"{'scenario':>8} {'gebouw':>6} {'cost (€)':>15} {'co2 (mg)':>15}")
    print("-" * 80)

    for r in items:
        scenario = r.get("scenario_id", "?")
        gebouw = r.get("gebouw_id", "?")
        cost = to_float(r.get("cost_total"), 0)
        co2 = to_float(r.get("totaal_mg_co2"), 0)

        print(f"{scenario:>8} {gebouw:>6} {cost:>15,.2f} {co2:>15,.2f}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, help="Pad naar scenario_results.jsonl")
    parser.add_argument("--top", type=int, default=3, help="Aantal resultaten tonen")
    args = parser.parse_args()

    rows = list(read_jsonl(Path(args.results)))
    if not rows:
        raise SystemExit("Geen records gevonden in results file.")

    top = args.top

    # Goedkoopste (laagste prijs, bij gelijke prijs laagste CO2)
    cheapest = sorted(
        rows,
        key=lambda r: (
            to_float(r.get("cost_total")),
            to_float(r.get("totaal_mg_co2")),
        ),
    )[:top]

    # Duurste (hoogste prijs, bij gelijke prijs laagste CO2)
    priciest = sorted(
        rows,
        key=lambda r: (
            -to_float(r.get("cost_total"), 0),
            to_float(r.get("totaal_mg_co2")),
        ),
    )[:top]

    # Laagste CO2 (laagste CO2, bij gelijke CO2 laagste prijs)
    lowest_co2 = sorted(
        rows,
        key=lambda r: (
            to_float(r.get("totaal_mg_co2")),
            to_float(r.get("cost_total")),
        ),
    )[:top]

    show(f"TOP {top} GOEDKOOPSTE", cheapest)
    show(f"TOP {top} DUURSTE", priciest)
    show(f"TOP {top} MINSTE CO2 (mg)", lowest_co2)


if __name__ == "__main__":
    main()