#!/usr/bin/env python3
# scripts/compute_results.py
#
# Verwacht scenario-formaat:
#   {"scenario_id":1,"keuzes":{"01":"34_33_10_010","02":"NONE",...}}

import argparse, json
from pathlib import Path

M2_COL = {
    "VASTGLAS": "VASTGLAS_m2",
    "METSELWERK": "METSELWERK_m2",
    "DAKOPPERVLAK": "DAKOPPERVLAK_m2",
    "VLOER/BODEM": "VLOER_BODEM_m2",
    "VLOER_BODEM": "VLOER_BODEM_m2",
}
M1_COL = {"KOZIJNEN": "KOZIJNEN_m1"}
STUK_COL = {"DEUR": "DEUR_stuks"}

def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                yield json.loads(ln)

def fnum(x, default=0.0):
    if x is None: return default
    if isinstance(x, (int, float)): return float(x)
    try: return float(str(x).strip().replace(",", "."))
    except Exception: return default

def qty(building, mat):
    enh = str(mat.get("enh", "")).strip().lower()
    drone = str(mat.get("input_dronescan", "")).strip().upper()

    if enh == "m2":
        col = M2_COL.get(drone, f"{drone.replace('/','_')}_m2")
        return fnum(building.get(col), 0.0)

    if enh == "m1":
        col = M1_COL.get(drone, f"{drone.replace('/','_')}_m1")
        return fnum(building.get(col), 0.0)

    if enh in ("stuk", "stuks"):
        if drone in STUK_COL:
            return fnum(building.get(STUK_COL[drone]), 0.0)
        col = f"{drone.replace('/','_')}_stuks"
        v = building.get(col)
        return fnum(v, 1.0) if v is not None else 1.0

    return 0.0

def mg_per_unit(mat):
    enh = str(mat.get("enh", "")).strip().lower()
    if enh == "m2": return fnum(mat.get("mg_co2_m2"), 0.0)
    if enh in ("stuk", "stuks"): return fnum(mat.get("mg_co2_stuk"), 0.0)
    if enh == "m1": return fnum(mat.get("mg_co2_m1"), 0.0)
    return 0.0

def load_building(buildings_path: Path, gebouw_id: int):
    for b in read_jsonl(buildings_path):
        gid = b.get("gebouw_id", b.get("id", b.get("building_id")))
        if gid == gebouw_id:
            return b
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--materials", default="materials.jsonl")
    ap.add_argument("--scenarios", default="scenarios.jsonl")
    ap.add_argument("--buildings", default="gebouwgegevens.jsonl")
    ap.add_argument("--gebouw-id", type=int, required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-scenarios", type=int, default=None)
    args = ap.parse_args()

    mats = {}
    for m in read_jsonl(Path(args.materials)):
        mid = m.get("material_id")
        if mid:
            mats[str(mid).strip()] = m

    building = load_building(Path(args.buildings), args.gebouw_id)
    if building is None:
        raise SystemExit(f"Geen gebouw gevonden met gebouw_id={args.gebouw_id} in {args.buildings}")

    out_path = Path(args.out) if args.out else Path(f"scenario_results_gebouw_{args.gebouw_id}.jsonl")

    with out_path.open("w", encoding="utf-8") as f_out:
        n = 0
        for scen in read_jsonl(Path(args.scenarios)):
            n += 1
            if args.max_scenarios and n > args.max_scenarios:
                break

            sid = scen.get("scenario_id")
            keuzes = scen.get("keuzes") or {}

            selected_ids = [v for v in keuzes.values() if v and v != "NONE"]

            cost_total = 0.0
            mg_total = 0.0
            for mid in selected_ids:
                mat = mats.get(str(mid).strip())
                if not mat:
                    continue
                q = qty(building, mat)
                cost_total += fnum(mat.get("prijs_norm"), 0.0) * q
                mg_total += mg_per_unit(mat) * q

            f_out.write(json.dumps({
                "gebouw_id": args.gebouw_id,
                "scenario_id": sid,
                "cost_total": int(round(cost_total)),
                "mg_co2_total": int(round(mg_total)),
            }, ensure_ascii=False) + "\n")

    print(f"OK -> {out_path}")

if __name__ == "__main__":
    main()
