#!/usr/bin/env python3
# Usage:
# python scripts/generate_onderdelen.csv [onderdelen.jsonl]

import csv
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_onderdelen.py materials.csv [onderdelen.jsonl]")
        raise SystemExit(1)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("onderdelen.jsonl")

    categorie_set = set()

    with src.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            cat = (row.get("Categorie") or "").strip()
            if cat:
                categorie_set.add(cat)

    # Sorteer voor stabiele output
    categorie_list = sorted(categorie_set)

    with out.open("w", encoding="utf-8") as f_out:
        for i, cat in enumerate(categorie_list, start=1):
            onderdeel = {
                "onderdeel_id": str(i).zfill(2),
                "categorie": cat
            }
            f_out.write(json.dumps(onderdeel, ensure_ascii=False) + "\n")

    print(f"OK -> {out}")


if __name__ == "__main__":
    main()
