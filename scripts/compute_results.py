#!/usr/bin/env python3
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
STUK_COL = {"DEUR": "DEUR_stuks"}  # deuren: leeg=0, installaties: default 1


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                yield json.loads(ln)


def fnum(x, default=0.0):
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip().replace(",", "."))
    except Exception:
        return default


def option_id(m):
    inp = str(m.get("input_dronescan", "UNKNOWN")).strip().upper()
    bh = m.get("bh"); bp = m.get("bp"); bd = m.get("bd")

    try: bh_str = f"{int(bh)}"
    except Exception: bh_str = str(bh).strip()

    try: bp_str = ("%g" % float(bp)).replace(".", "p")
    except Exception: bp_str = str(bp).strip().replace(".", "p")

    try: bd_str = f"{int(bd):03d}"
    except Exception: bd_str = str(bd).strip()

    return f"{inp}_BH{bh_str}_BP{bp_str}_BD{bd_str}"


def qty(building, mat):
    enh = str(mat.get("enh", "")).strip().lower()
    drone = str(mat.get("input_dronescan", "")).strip().upper()

    if enh == "m2":
        col = M2_COL.get(drone, f"{drone.replace('/','_')}_m2")
        return fnum(building.get(col), 0.0)

    if enh == "m1":
        col = M1_COL.get(drone, f"{drone.replace('/','_')}_m1")
        return fnum(building.get(col), 0.0)

    if enh == "stuk":
        if drone in STUK_COL:
            return fnum(building.get(STUK_COL[drone]), 0.0)  # deuren: leeg=0
        # installaties/overig: default 1 (tenzij je een kolom hebt)
        col_guess = f"{drone.replace('/','_')}_stuks"
        v = building.get(col_guess)
        return fnum(v, 1.0) if v is not None else 1.0

    return 0.0


def mg_per_unit(mat):
    enh = str(mat.get("enh", "")).strip().lower()
    if enh == "m2":
        return fnum(mat.get("mg_co2_m2"), 0.0)
    if enh == "stuk":
        return fnum(mat.get("mg_co2_stuk"), 0.0)
    if enh == "m1":
        return fnum(mat.get("mg_co2_m1"), 0.0)
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
    ap.add_argument("--gebouw-id", type=int, required=True, help="Welk gebouw_id wil je doorrekenen?")
    ap.add_argument("--out", default=None, help="Output bestand; default: scenario_results_gebouw_<id>.jsonl")
    ap.add_argument("--max-scenarios", type=int, default=None)
    args = ap.parse_args()

    mats = {option_id(m): m for m in read_jsonl(Path(args.materials))}

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
            skey = scen.get("scenario_key")
            selected = scen.get("selected_option_ids", [])

            chosen = [mats[oid] for oid in selected if oid in mats]

            cost_total = 0.0
            mg_total = 0.0
            for m in chosen:
                q = qty(building, m)
                cost_total += fnum(m.get("prijs_norm"), 0.0) * q
                mg_total += mg_per_unit(m) * q

            f_out.write(json.dumps({
                "gebouw_id": args.gebouw_id,
                "scenario_id": sid,
                "scenario_key": skey,
                "cost_total": int(round(cost_total)),
                "mg_co2_total": int(round(mg_total)),
            }, ensure_ascii=False) + "\n")

    print(f"OK -> {out_path}")


if __name__ == "__main__":
    main()
