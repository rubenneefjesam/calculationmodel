#!/usr/bin/env python3
#
# gen_ranks.py
#
# Leest results_gebouw_xxx.jsonl en genereert top 10 rankings:
#   - top10_duurste
#   - top10_goedkoopste
#   - top10_meeste_co2
#   - top10_minste_co2
#   - top10_optimaal (50/50 prijs + co2 genormaliseerd)
#
# Gebruik:
#   python scripts/gen_ranks.py
#   python scripts/gen_ranks.py --gebouw gebouw_002
#

import argparse
import json
from pathlib import Path


def load_results(path: Path) -> list:
    results = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def bereken_optimaal_score(results: list) -> list:
    """Voeg genormaliseerde 50/50 score toe aan elk resultaat."""
    prijzen = [r["cost_total"] for r in results]
    co2s    = [r["co2_total"]  for r in results]

    p_min, p_max = min(prijzen), max(prijzen)
    c_min, c_max = min(co2s),    max(co2s)

    for r in results:
        p_norm = (r["cost_total"] - p_min) / (p_max - p_min) if p_max != p_min else 0
        c_norm = (r["co2_total"]  - c_min) / (c_max - c_min) if c_max != c_min else 0
        r["optimaal_score"] = round((p_norm + c_norm) / 2, 6)

    return results


def top10(results: list, key: str, reverse: bool) -> list:
    ranked = sorted(results, key=lambda r: r[key], reverse=reverse)[:10]
    # Verwijder optimaal_score uit output (intern gebruik)
    return [{k: v for k, v in r.items() if k != "optimaal_score"} for r in ranked]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gebouw",   default=None,                                 help="Gebouw ID")
    parser.add_argument("--results",  default=None,                                 help="Pad naar results_gebouw_xxx.jsonl")
    parser.add_argument("--out",      default=None,                                 help="Output pad")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]

    # Bepaal input pad
    if args.results:
        results_path = root / args.results
    elif args.gebouw:
        results_path = root / f"data/output/results_{args.gebouw}.jsonl"
    else:
        # Zoek automatisch het eerste results bestand
        matches = list((root / "data/output").glob("results_gebouw_*.jsonl"))
        if not matches:
            print("ERROR: geen results bestand gevonden in data/output/")
            return
        results_path = matches[0]

    gebouw_id = results_path.stem.replace("results_", "")

    out_path = root / (args.out or f"data/output/ranks_{gebouw_id}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Laden resultaten: {results_path.name}")
    results = load_results(results_path)
    print(f"  {len(results):,} scenario's geladen")

    print("Berekenen scores en rankings...")
    results = bereken_optimaal_score(results)

    output = {
        "gebouw_id":          gebouw_id,
        "totaal_scenarios":   len(results),
        "top10_duurste":      top10(results, "cost_total",     reverse=True),
        "top10_goedkoopste":  top10(results, "cost_total",     reverse=False),
        "top10_meeste_co2":   top10(results, "co2_total",      reverse=True),
        "top10_minste_co2":   top10(results, "co2_total",      reverse=False),
        "top10_optimaal":     top10(results, "optimaal_score", reverse=False),
    }

    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nOK -> {out_path}")
    print(f"Totaal scenario's: {len(results):,}")
    print(f"\n--- TOP 3 GOEDKOOPSTE ---")
    for i, s in enumerate(output["top10_goedkoopste"][:3], 1):
        print(f"  #{i}  €{s['cost_total']:>12,.2f}  |  CO2: {s['co2_total']:>12,.2f}")
    print(f"\n--- TOP 3 MINSTE CO2 ---")
    for i, s in enumerate(output["top10_minste_co2"][:3], 1):
        print(f"  #{i}  CO2: {s['co2_total']:>12,.2f}  |  €{s['cost_total']:>12,.2f}")
    print(f"\n--- TOP 3 OPTIMAAL ---")
    for i, s in enumerate(output["top10_optimaal"][:3], 1):
        print(f"  #{i}  €{s['cost_total']:>12,.2f}  |  CO2: {s['co2_total']:>12,.2f}")


if __name__ == "__main__":
    main()