#!/usr/bin/env python3
# Usage: python scripts/convert_csv_to_jsonl.py materials.csv [materials.jsonl]

import csv, json, re, sys
from pathlib import Path

NULLS = {"", "x", "X", "-", "—", "n.v.t.", "nvt", "na", "null", "None"}

def snake(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[\s/]+", "_", s)
    s = re.sub(r"[-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return re.sub(r"_+", "_", s).strip("_") or "col"

def clean(v):
    if v is None: return None
    v = v.strip().replace("\ufeff", "").replace("\u00a0", " ")
    return None if v in NULLS else v

def material_id(bh, bp, bd) -> str:
    bh = clean(bh) or "NA"
    bp = (clean(bp) or "NA").replace(",", ".")
    try: bp = ("%g" % float(bp))  # 37.120 -> 37.12
    except Exception: pass
    bp = str(bp).replace(".", "_")
    bd = clean(bd) or "NA"
    bd = bd.zfill(3) if str(bd).isdigit() else bd
    return f"{bh}_{bp}_{bd}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_csv_to_jsonl.py materials.csv [materials.jsonl]")
        raise SystemExit(1)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".jsonl")

    with src.open("r", encoding="utf-8-sig", newline="") as f_in, out.open("w", encoding="utf-8") as f_out:
        r = csv.DictReader(f_in, delimiter=";")
        keys = r.fieldnames or []
        keymap = {k: snake(k) for k in keys}

        for row in r:
            obj = {keymap[k]: clean(v) for k, v in row.items() if k is not None}
            mid = material_id(obj.get("bh"), obj.get("bp"), obj.get("bd"))
            obj.pop("material_id", None)  # voorkom dubbele key
            out_obj = {"material_id": mid}
            out_obj.update(obj)
            f_out.write(json.dumps(out_obj, ensure_ascii=False) + "\n")

    print(f"OK -> {out}")

if __name__ == "__main__":
    main()
