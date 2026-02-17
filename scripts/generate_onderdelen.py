#!/usr/bin/env python3

import csv
import json
from pathlib import Path


def main():
    # project root = 1 niveau boven scripts/
    root = Path(__file__).resolve().parents[1]

    src = root / "data" / "brondata" / "materials.csv"
    out = root / "data" / "brondata" / "onderdelen.jsonl"

    if not src.exists():
        print(f"ERROR: materials.csv niet gevonden -> {src}")
        return

    categorie_set = set()

    with src.open("r", encoding="cp1252", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            cat = (row.get("Categorie") or "").strip()
            if cat:
                categorie_set.add(cat)

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
