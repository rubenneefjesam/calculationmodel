#!/usr/bin/env python3
#
# gen_scenarios.py
#
# Genereert alle mogelijke scenario's op basis van:
#   - data/gebouwdata/gebouwgegevens.json   (gebouwafmetingen + opties)
#   - data/brondata/materials.jsonl         (materialen per categorie)
#   - data/brondata/onderdelen.jsonl        (categorie -> onderdeel_id mapping)
#
# Voorbeelden:
#   python scripts/gen_scenarios.py
#   python scripts/gen_scenarios.py --gebouw gebouw_002
#   python scripts/gen_scenarios.py --max-scenarios 10000
#

import argparse
import itertools
import json
from pathlib import Path
from typing import Dict, List, Optional

PANEEL_M2_PER_STUK = 1.7

# Vaste mapping: (categorie, veld_in_afmetingen, enh, conditie_veld, conditie_waarde)
CATEGORIE_MAP = [
    ("Beglazing",           "beglazing_m2",  "m2",    None,      None),
    ("Gevelisolatie",       "gevel_m2",      "m2",    None,      None),
    ("Deuren",              "deuren_stuks",  "stuks", None,      None),
    ("Hellend dakisolatie", "dak_m2",        "m2",    "daktype", "schuin"),
    ("Plat dakisolatie",    "dak_m2",        "m2",    "daktype", "plat"),
    ("Vloerisolatie",       "vloer_m2",      "m2",    None,      None),
    ("Kozijnen",            "kozijnen_m1",   "m1",    None,      None),
]

OPTIE_MAP = [
    ("Panelen",       "panelen",      "stuks", lambda afm: afm.get("dak_m2", 0) / PANEEL_M2_PER_STUK),
    ("Zonne-energie", "zonnepanelen", "stuks", lambda afm: afm.get("dak_m2", 0) / PANEEL_M2_PER_STUK),
    ("Ventilatie",    "ventilatie",   "stuks", lambda afm: 1),
]

VERWARMING_VOORKEUR_MAP = {
    "ketel":           "Verwarming - Ketel",
    "warmtepomp":      "Verwarming - Warmtepomp",
    "stadsverwarming": "Stadsverwarming",
}


def read_jsonl(path: Path) -> List[Dict]:
    items = []
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                items.append(json.loads(ln))
    return items


def load_gebouw(path: Path, gebouw_id: Optional[str]) -> Dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        if gebouw_id:
            for g in data:
                if str(g.get("gebouw_id")) == gebouw_id:
                    return g
            raise ValueError(f"Gebouw '{gebouw_id}' niet gevonden in {path}")
        return data[0]
    return data


def load_onderdeel_map(path: Path) -> Dict[str, str]:
    """Geeft categorie -> onderdeel_id mapping."""
    result = {}
    for item in read_jsonl(path):
        cat = item.get("categorie", "").strip()
        oid = item.get("onderdeel_id", "").strip()
        if cat and oid:
            result[cat] = oid
    return result


def resolve_actief(gebouw: Dict) -> List[Dict]:
    afm  = gebouw.get("afmetingen", {})
    opts = gebouw.get("opties", {})
    actief = []

    for categorie, veld, enh, cond_veld, cond_waarde in CATEGORIE_MAP:
        if cond_veld and afm.get(cond_veld) != cond_waarde:
            continue
        waarde = afm.get(veld)
        if waarde and float(waarde) > 0:
            actief.append({"categorie": categorie, "waarde": float(waarde), "enh": enh})

    for categorie, optie_veld, enh, waarde_fn in OPTIE_MAP:
        if opts.get(optie_veld):
            waarde = waarde_fn(afm)
            if waarde and float(waarde) > 0:
                actief.append({"categorie": categorie, "waarde": round(float(waarde), 2), "enh": enh})

    if opts.get("verwarming"):
        voorkeur = opts.get("verwarming_voorkeur")
        if voorkeur and voorkeur in VERWARMING_VOORKEUR_MAP:
            cats = [VERWARMING_VOORKEUR_MAP[voorkeur]]
        else:
            cats = list(VERWARMING_VOORKEUR_MAP.values())
        for cat in cats:
            actief.append({"categorie": cat, "waarde": 1, "enh": "stuks"})

    return actief


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gebouw",        default=None,                                  help="Gebouw ID")
    parser.add_argument("--gebouwdata",    default="data/gebouwdata/gebouwgegevens.json",  help="Pad naar gebouwgegevens.json")
    parser.add_argument("--materials",     default="data/brondata/materials.jsonl",        help="Pad naar materials.jsonl")
    parser.add_argument("--onderdelen",    default="data/brondata/onderdelen.jsonl",       help="Pad naar onderdelen.jsonl")
    parser.add_argument("--out",           default="data/output/scenarios.jsonl",          help="Output pad")
    parser.add_argument("--max-scenarios", type=int, default=None,                         help="Maximaal aantal scenario's")
    parser.add_argument("--add-none",      action="store_true",                            help="Voeg NONE-optie toe per onderdeel")
    args = parser.parse_args()

    root        = Path(__file__).resolve().parents[1]
    gebouw      = load_gebouw(root / args.gebouwdata, args.gebouw)
    mats        = read_jsonl(root / args.materials)
    oid_map     = load_onderdeel_map(root / args.onderdelen)
    out_path    = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    by_cat: Dict[str, List[Dict]] = {}
    for m in mats:
        cat = m.get("categorie", "").strip()
        if cat:
            by_cat.setdefault(cat, []).append(m)

    actief = resolve_actief(gebouw)

    if not actief:
        print("Geen actieve onderdelen gevonden.")
        return

    print(f"Gebouw: {gebouw.get('gebouw_id')}")
    print(f"Actieve onderdelen ({len(actief)}):")

    opties_per_cat = []
    totaal = 1

    for item in actief:
        cat   = item["categorie"]
        oid   = oid_map.get(cat, cat)  # fallback op naam als ID niet gevonden
        maten = by_cat.get(cat, [])

        if not maten:
            print(f"  WAARSCHUWING: geen materialen voor '{cat}' ({oid}), overgeslagen")
            continue

        material_ids = sorted(set(m["material_id"] for m in maten))
        if args.add_none:
            material_ids = ["NONE"] + material_ids

        print(f"  {len(material_ids):3d}x  [{oid}] {cat}  ({item['waarde']} {item['enh']})")
        totaal *= len(material_ids)
        opties_per_cat.append((oid, material_ids))

    print(f"\nTotaal scenario's: {totaal:,}")
    print("Genereren...")

    oid_namen     = [o for o, _ in opties_per_cat]
    optie_lijsten = [ids for _, ids in opties_per_cat]

    scenario_id = 0

    with out_path.open("w", encoding="utf-8") as f_out:
        for combo in itertools.product(*optie_lijsten):
            scenario_id += 1
            record = {
                "scenario_id": scenario_id,
                "gebouw_id":   gebouw.get("gebouw_id"),
                "keuzes":      {oid_namen[i]: combo[i] for i in range(len(oid_namen))},
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

            if args.max_scenarios and scenario_id >= args.max_scenarios:
                break

    print(f"OK -> {out_path}")
    print(f"Scenario's gegenereerd: {scenario_id:,}")


if __name__ == "__main__":
    main()