#!/usr/bin/env python3

import csv
import json
import re
from pathlib import Path

# Waarden die als NULL moeten worden behandeld
NULLS = {"", "x", "X", "-", "—", "n.v.t.", "nvt", "na", "null", "None"}

# Velden die numeriek moeten worden
NUMERIC_FIELDS = {
    "mg_co2_stuk",
    "mg_co2_m2",
    "prijs_norm",
    "duurzaam",
    "rd_m2k",
    "dikte_mm",
}

def snake(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[\s/]+", "_", s)
    s = re.sub(r"[-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return re.sub(r"_+", "_", s).strip("_") or "col"

def clean(v):
    if v is None:
        return None
    v = v.strip().replace("\ufeff", "").replace("\u00a0", " ")
    return None if v in NULLS else v

def parse_numeric(value):
    if value is None:
        return None
    value = value.replace(",", ".")
    try:
        if "." in value:
            return float(value)
        return int(value)
    except Exception:
        return value

def material_id(bh, bp, bd) -> str:
    bh = clean(bh) or "NA"

    bp = clean(bp) or "NA"
    bp = bp.replace(",", ".")
    try:
        bp = ("%g" % float(bp))
    except Exception:
        pass
    bp = str(bp).replace(".", "_")

    bd = clean(bd) or "NA"
    bd = bd.zfill(3) if str(bd).isdigit() else bd

    return f"{bh}_{bp}_{bd}"

def load_onderdelen_map(root: Path) -> dict:
    m = {}
    p = root / "data" / "brondata" / "onderdelen.jsonl"
    if not p.exists():
        return m

    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        o = json.loads(ln)
        oid = str(o.get("onderdeel_id", "")).strip()
        cat = str(o.get("categorie", "")).strip().upper()
        if oid and cat:
            m[cat] = oid

    return m

def main():
    root = Path(__file__).resolve().parents[1]

    src = root / "data" / "brondata" / "materials.csv"
    out = root / "data" / "brondata" / "materials.jsonl"

    if not src.exists():
        print(f"ERROR: materials.csv niet gevonden -> {src}")
        return

    omap = load_onderdelen_map(root)

    with src.open("r", encoding="cp1252", newline="") as f_in, \
         out.open("w", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in, delimiter=";")
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        keymap = {k: snake(k) for k in reader.fieldnames}

        for row in reader:
            obj = {}
            for k, v in row.items():
                key = keymap[k]
                value = clean(v)

                if key in NUMERIC_FIELDS:
                    value = parse_numeric(value)

                obj[key] = value

            mid = material_id(obj.get("bh"), obj.get("bp"), obj.get("bd"))

            categorie = (obj.get("categorie") or "").strip().upper()
            onderdeel_id = omap.get(categorie)

            obj.pop("material_id", None)
            obj.pop("onderdeel_id", None)

            out_obj = {
                "material_id": mid,
                "onderdeel_id": onderdeel_id,
            }

            out_obj.update(obj)

            f_out.write(json.dumps(out_obj, ensure_ascii=False) + "\n")

    print(f"OK -> {out}")

if __name__ == "__main__":
    main()
