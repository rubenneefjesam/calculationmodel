#!/usr/bin/env python3
# scripts/rank_results.py
import argparse, json
from pathlib import Path

def read_jsonl(p: Path):
    with p.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                yield json.loads(ln)

def show(title, items):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(f"{'scenario':>8} {'gebouw':>6} {'cost':>10} {'co2_mg':>10}")
    print("-" * 80)
    for r in items:
        print(f"{str(r.get('scenario_id')):>8} {str(r.get('gebouw_id')):>6} {str(r.get('cost_total')):>10} {str(r.get('mg_co2_total')):>10}")
    print("=" * 80)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--top", type=int, default=3)
    args = ap.parse_args()

    rows = list(read_jsonl(Path(args.results)))
    if not rows:
        raise SystemExit("Geen records gevonden in results file.")

    top = args.top
    cheapest   = sorted(rows, key=lambda r: (r.get("cost_total", 10**18), r.get("mg_co2_total", 10**18)))[:top]
    priciest   = sorted(rows, key=lambda r: (-(r.get("cost_total", -1)), r.get("mg_co2_total", 10**18)))[:top]
    lowest_co2 = sorted(rows, key=lambda r: (r.get("mg_co2_total", 10**18), r.get("cost_total", 10**18)))[:top]

    show(f"TOP {top} GOEDKOOPSTE", cheapest)
    show(f"TOP {top} DUURSTE", priciest)
    show(f"TOP {top} MINSTE CO2 (mg)", lowest_co2)

if __name__ == "__main__":
    main()
