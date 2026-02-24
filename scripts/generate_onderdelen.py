#!/usr/bin/env python3

import csv
import json
from pathlib import Path


def norm_enh(enh: str) -> str:
    e = (enh or "").strip().lower()
    if e == "stuk":
        return "stuks"
    return e


def main():
    root = Path(__file__).resolve().parents[1]

    src = root / "data" / "brondata" / "materials.csv"
    out = root / "data" / "brondata" / "onderdelen.jsonl"

    if not src.exists():
        print(f"ERROR: materials.csv niet gevonden -> {src}")
        return

    # categorie -> set(enh)
    cat_to_enh = {}

    with src.open("r", encoding="cp1252", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        reader.fieldnames = [h.strip() for h in reader.fieldnames]

        for row in reader:
            cat = (row.get("Categorie") or "").strip()
            enh = norm_enh(row.get("Enh") or row.get("ENH") or "")

            if not cat:
                continue

            cat_to_enh.setdefault(cat, set())

            # enh is optioneel; maar als het er is, opslaan
            if enh:
                cat_to_enh[cat].add(enh)

    categorie_list = sorted(cat_to_enh.keys())

    with out.open("w", encoding="utf-8") as f_out:
        for i, cat in enumerate(categorie_list, start=1):
            onderdeel = {
                "onderdeel_id": str(i).zfill(2),
                "categorie": cat,
                "enh": sorted(cat_to_enh[cat])  # lijst
            }
            f_out.write(json.dumps(onderdeel, ensure_ascii=False) + "\n")

    print(f"OK -> {out}")
    print(f"Categorieën: {len(categorie_list)}")


if __name__ == "__main__":
    main()
