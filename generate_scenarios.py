#!/usr/bin/env python3
# generate_scenarios.py
#
# Voorbeelden:
#   python generate_scenarios.py --materials materials.jsonl --out scenarios.jsonl
#   python generate_scenarios.py --include Beglazing Gevelisolatie
#   python generate_scenarios.py --add-none
#
# Output: scenarios.jsonl (1 scenario per regel)

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


GROUP_FIELD = "categorie"       # jij wil groeperen op categorie
NAME_FIELD = "naam"
DRONE_FIELD = "input_dronescan" # blijft nuttig in option_id


def make_option_id(m: Dict[str, Any]) -> str:
    """
    Stabiele option_id op basis van input_dronescan + BH/BP/BD.
    Voorbeeld: METSELWERK_BH37_BP41p2_BD030
    """
    inp = str(m.get(DRONE_FIELD, "UNKNOWN")).strip().upper()

    bh = m.get("bh")
    bp = m.get("bp")
    bd = m.get("bd")

    try:
        bh_str = f"{int(bh)}"
    except Exception:
        bh_str = str(bh).strip()

    try:
        bp_g = ("%g" % float(bp)).replace(".", "p")
    except Exception:
        bp_g = str(bp).strip().replace(".", "p")

    try:
        bd_str = f"{int(bd):03d}"
    except Exception:
        bd_str = str(bd).strip()

    return f"{inp}_BH{bh_str}_BP{bp_g}_BD{bd_str}"


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            items.append(json.loads(ln))
    return items


def stable_sort_key(m: Dict[str, Any]) -> Tuple:
    return (
        str(m.get(GROUP_FIELD, "")),
        str(m.get(DRONE_FIELD, "")),
        int(m["bh"]) if isinstance(m.get("bh"), (int, float)) else 10**9,
        float(m["bp"]) if isinstance(m.get("bp"), (int, float)) else 10**9,
        int(m["bd"]) if isinstance(m.get("bd"), (int, float)) else 10**9,
        str(m.get(NAME_FIELD, "")),
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--materials", default="materials.jsonl", help="pad naar materials.jsonl")
    p.add_argument("--out", default="scenarios.jsonl", help="output jsonl met scenario's")
    p.add_argument("--include", nargs="*", default=None,
                   help="optioneel: alleen deze categorie-waarden meenemen (bv. Beglazing Gevelisolatie)")
    p.add_argument("--add-none", action="store_true",
                   help="voeg per categorie ook een NONE-optie toe (geen maatregel)")
    args = p.parse_args()

    mats = read_jsonl(Path(args.materials))

    include = None
    if args.include:
        include = {x.strip().upper() for x in args.include}

    # group by categorie
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for m in mats:
        g = str(m.get(GROUP_FIELD, "")).strip()
        if not g:
            continue
        g_u = g.upper()
        if include is not None and g_u not in include:
            continue
        groups.setdefault(g_u, []).append(m)

    group_keys = sorted(groups.keys())
    option_lists: List[List[Dict[str, Any]]] = []

    for g in group_keys:
        opts_raw = sorted(groups[g], key=stable_sort_key)

        # dedupe op basis van option_id (handig bij dubbele dakregels)
        seen = set()
        opts: List[Dict[str, Any]] = []
        for o in opts_raw:
            oid = make_option_id(o)
            if oid in seen:
                continue
            seen.add(oid)
            o["_option_id"] = oid
            o["_group"] = g
            opts.append(o)

        if args.add_none:
            opts = [{"_option_id": "NONE", "_group": g, NAME_FIELD: "NONE"}] + opts

        option_lists.append(opts)

    # cartesian product -> scenarios.jsonl
    scenario_id = 0
    out_path = Path(args.out)

    with out_path.open("w", encoding="utf-8") as f_out:
        for combo in itertools.product(*option_lists):
            scenario_id += 1

            keuzes = {c["_group"]: c["_option_id"] for c in combo}
            selected_ids = [c["_option_id"] for c in combo if c["_option_id"] != "NONE"]

            key_src = "|".join([f"{k}={keuzes[k]}" for k in sorted(keuzes.keys())])
            scenario_key = hashlib.sha1(key_src.encode("utf-8")).hexdigest()[:12]

            record = {
                "scenario_id": scenario_id,
                "scenario_key": scenario_key,
                "keuzes": keuzes,                    # per categorie -> option_id
                "selected_option_ids": selected_ids   # platte lijst
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"OK -> {out_path} (scenario's: {scenario_id}, groepen: {len(group_keys)})")
    print("Gebruikte categorie-groepen:", ", ".join(group_keys))


if __name__ == "__main__":
    main()
