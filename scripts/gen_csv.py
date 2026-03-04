#!/usr/bin/env python3

import csv
import json
import re
from pathlib import Path

NULLS = {"", "x", "X", "-", "—", "n.v.t.", "nvt", "na", "null", "None"}

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
    v = v.replace("\ufffd", "").replace("\x80", "").replace("€", "").strip()
    return None if v in NULLS else v


def parse_numeric(value):
    if value is None:
        return None
    value = value.replace("\x80", "").replace("€", "").replace("\xef\xbf\xbd", "").strip()
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(".", "")
    try:
        f = float(value)
        return int(f) if f == int(f) else f
    except Exception:
        return None


def material_id(bh, bp, bd) -> str:
    bh = clean(bh) or "NA"

    bp = clean(bp) or "NA"
    bp = bp.replace(",", ".")
    try:
        bp = "%g" % float(bp)
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
        print("WAARSCHUWING: onderdelen.jsonl niet gevonden, onderdeel_id wordt None")
        return m

    for ln in p.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        o = json.loads(ln)
        oid = str(o.get("onderdeel_id", "")).strip()
        cat = str(o.get("categorie", "")).strip()
        if oid and cat:
            m[cat] = oid

    return m


def resolve_onderdeel_id(categorie: str, omap: dict) -> str | None:
    if categorie in omap:
        return omap[categorie]
    for key, oid in omap.items():
        if categorie.startswith(key):
            return oid
    return None


def norm_enh(enh: str) -> str:
    e = (enh or "").strip().lower()
    return "stuks" if e == "stuk" else e


def main():
    root = Path(__file__).resolve().parents[1]

    src = root / "data" / "brondata" / "materialenlijst.csv"
    out = root / "data" / "brondata" / "materials.jsonl"

    if not src.exists():
        print(f"ERROR: materialenlijst.csv niet gevonden -> {src}")
        return

    omap = load_onderdelen_map(root)

    skipped = 0
    written = 0

    with src.open("r", encoding="utf-8", newline="") as f_in, \
         out.open("w", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in, delimiter=";")
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        keymap = {k: snake(k) for k in reader.fieldnames}

        for row in reader:
            obj = {}
            for k, v in row.items():
                key = keymap.get(k, snake(k))
                value = clean(v)
                if key in NUMERIC_FIELDS:
                    value = parse_numeric(value)
                obj[key] = value

            categorie = (obj.get("categorie") or "").strip()
            if not categorie:
                skipped += 1
                continue

            mid = material_id(obj.get("bh"), obj.get("bp"), obj.get("bd"))
            onderdeel_id = resolve_onderdeel_id(categorie, omap)
            enh = norm_enh(obj.get("enh") or "")

            if enh == "stuks":
                co2_value = obj.get("mg_co2_stuk")
            else:
                co2_value = obj.get("mg_co2_m2")

            prijs = obj.get("prijs_norm")

            out_obj = {
                "material_id":  mid,
                "onderdeel_id": onderdeel_id,
                "categorie":    categorie,
                "naam":         obj.get("naam"),
                "materiaal":    obj.get("materiaal"),
                "dikte_mm":     obj.get("dikte_mm"),
                "rd_m2k":       obj.get("rd_m2k"),
                "enh":          enh,
                "co2_value":    co2_value,
                "prijs":        prijs,
                "omschrijving": obj.get("omschrijving"),
                "duurzaam":     obj.get("duurzaam"),
                "toepassing":   obj.get("toepassing"),
                "opmerking":    obj.get("opmerking"),
            }

            f_out.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            written += 1

    print(f"OK -> {out}")
    print(f"Geschreven: {written} | Overgeslagen: {skipped}")


if __name__ == "__main__":
    main()