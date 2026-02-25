#!/usr/bin/env python3
#
# generate_scenarios.py
#
# Voorbeelden:
#   python scripts/generate_scenarios.py --gebouw 1
#   python scripts/generate_scenarios.py --gebouw 1 --add-none
#   python scripts/generate_scenarios.py --gebouw 1 --max-scenarios 10000
#   python scripts/generate_scenarios.py --gebouw 1 --include 01 02 03
#

import argparse
import itertools
import json
from pathlib import Path
from typing import Dict, List, Optional


def read_jsonl(path: Path) -> List[Dict]:
    items = []
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                items.append(json.loads(ln))
    return items


def read_gebouw(path: Path, gebouw_id: int) -> Optional[Dict]:
    for g in read_jsonl(path):
        if g.get("gebouw_id") == gebouw_id:
            return g
    return None


def heeft_factor(onderdeel_id: str, gebouw: Dict) -> bool:
    """
    Controleert of een onderdeel een factor > 0 heeft in de gebouwgegevens.
    Zoekt op sleutels als '01_m2', '01_stuks' etc.
    """
    oid = str(onderdeel_id).strip()
    for key, value in gebouw.items():
        if key.startswith(f"{oid}_"):
            try:
                if float(value or 0) > 0:
                    return True
            except (TypeError, ValueError):
                pass
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gebouw",
        type=int,
        required=True,
        help="Gebouw ID om scenario's voor te genereren"
    )
    parser.add_argument(
        "--materials",
        default="data/brondata/materials.jsonl",
        help="Pad naar materials.jsonl"
    )
    parser.add_argument(
        "--gebouwdata",
        default="data/gebouwdata/gebouwgegevens.jsonl",
        help="Pad naar gebouwgegevens.jsonl"
    )
    parser.add_argument(
        "--out",
        default="data/output/scenarios.jsonl",
        help="Output pad voor scenario's"
    )
    parser.add_argument(
        "--include",
        nargs="*",
        help="Alleen deze onderdeel_id's meenemen (bijv: 01 02 03)"
    )
    parser.add_argument(
        "--add-none",
        action="store_true",
        help="Voeg NONE-optie toe per onderdeel"
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=None,
        help="Maximaal aantal scenario's genereren"
    )

    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    materials_path = root / args.materials
    gebouw_path    = root / args.gebouwdata
    output_path    = root / args.out

    output_path.parent.mkdir(exist_ok=True)

    # Laad gebouwgegevens
    gebouw = read_gebouw(gebouw_path, args.gebouw)
    if not gebouw:
        print(f"ERROR: Gebouw {args.gebouw} niet gevonden in {gebouw_path}")
        return

    mats = read_jsonl(materials_path)

    # ---------------------------
    # Groepeer per onderdeel_id
    # ---------------------------
    groups: Dict[str, List[str]] = {}

    for m in mats:
        onderdeel_id = str(m.get("onderdeel_id") or "").strip()
        material_id  = str(m.get("material_id")  or "").strip()

        if not onderdeel_id or not material_id:
            continue

        if args.include and onderdeel_id not in args.include:
            continue

        # Sla onderdelen over die geen factor > 0 hebben voor dit gebouw
        if not heeft_factor(onderdeel_id, gebouw):
            continue

        groups.setdefault(onderdeel_id, []).append(material_id)

    if not groups:
        print("Geen geldige onderdelen gevonden.")
        return

    # Deterministische volgorde
    group_keys = sorted(groups.keys())

    option_lists: List[List[str]] = []

    for gid in group_keys:
        opts = sorted(set(groups[gid]))  # dedupe + sort

        if args.add_none:
            opts = ["NONE"] + opts

        option_lists.append(opts)

    # ---------------------------
    # Scenario generatie
    # ---------------------------
    scenario_id = 0

    with output_path.open("w", encoding="utf-8") as f_out:
        for combo in itertools.product(*option_lists):

            scenario_id += 1

            keuzes = {
                group_keys[i]: combo[i]
                for i in range(len(group_keys))
            }

            record = {
                "scenario_id": scenario_id,
                "keuzes":      keuzes
            }

            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

            if args.max_scenarios and scenario_id >= args.max_scenarios:
                break

    print(f"OK -> {output_path}")
    print(f"Gebouw:               {args.gebouw}")
    print(f"Onderdelen actief:    {len(group_keys)} {group_keys}")
    print(f"Scenario's gegenereerd: {scenario_id}")


if __name__ == "__main__":
    main()