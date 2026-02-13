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
    # moet matchen met generate_scenarios.py
    inp = str(m.get("input_dronescan", "UNKNOWN")).strip().upper()
    bh = m.get("bh"); bp = m.get("bp"); bd = m.get("bd")

    try: bh_str = f"{int(bh)}"
    except Exception: bh_str = str(bh).strip()

    try: bp_str = ("%g" % float(bp)).replace(".", "p")
    except Exception: bp_str = str(bp).strip().replace(".", "p")

    try: bd_str = f"{int(bd):03d}"
    except Exception: bd_str = str(bd).strip()

    return f"{inp}_BH{bh_str}_BP{bp_str}_BD{bd_str}"


def qty_and_source(building, mat):
    enh = str(mat.get("enh", "")).strip().lower()
    drone = str(mat.get("input_dronescan", "")).strip().upper()

    if enh == "m2":
        col = M2_COL.get(drone, f"{drone.replace('/','_')}_m2")
        return fnum(building.get(col), 0.0), col

    if enh == "m1":
        col = M1_COL.get(drone, f"{drone.replace('/','_')}_m1")
        return fnum(building.get(col), 0.0), col

    if enh == "stuk":
        if drone in STUK_COL:
            col = STUK_COL[drone]
            return fnum(building.get(col), 0.0), col  # deuren: leeg=0
        # installaties/overig: default 1 (tenzij je een kolom hebt)
        col_guess = f"{drone.replace('/','_')}_stuks"
        if col_guess in building and building.get(col_guess) is not None:
            return fnum(building.get(col_guess), 1.0), col_guess
        return 1.0, "DEFAULT_1_STUK"

    return 0.0, "UNKNOWN_ENH"


def mg_per_unit(mat):
    enh = str(mat.get("enh", "")).strip().lower()
    if enh == "m2":
        return fnum(mat.get("mg_co2_m2"), 0.0), "mg_co2_m2"
    if enh == "stuk":
        return fnum(mat.get("mg_co2_stuk"), 0.0), "mg_co2_stuk"
    if enh == "m1":
        return fnum(mat.get("mg_co2_m1"), 0.0), "mg_co2_m1"
    return 0.0, "mg_co2_unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--materials", default="materials.jsonl")
    ap.add_argument("--scenarios", default="scenarios.jsonl")
    ap.add_argument("--buildings", default="gebouwgegevens.jsonl")
    ap.add_argument("--gebouw-id", type=int, required=True)
    ap.add_argument("--scenario-id", type=int, required=True)
    args = ap.parse_args()

    mats = {option_id(m): m for m in read_jsonl(Path(args.materials))}

    building = None
    for b in read_jsonl(Path(args.buildings)):
        if b.get("gebouw_id") == args.gebouw_id:
            building = b
            break
    if building is None:
        raise SystemExit(f"Gebouw {args.gebouw_id} niet gevonden in {args.buildings}")

    scenario = None
    for s in read_jsonl(Path(args.scenarios)):
        if int(s.get("scenario_id")) == args.scenario_id:
            scenario = s
            break
    if scenario is None:
        raise SystemExit(f"Scenario {args.scenario_id} niet gevonden in {args.scenarios}")

    selected = scenario.get("selected_option_ids", [])
    chosen = []
    missing = []
    for oid in selected:
        m = mats.get(oid)
        if m is None:
            missing.append(oid)
        else:
            chosen.append((oid, m))

    print("=" * 90)
    print(f"EXPLAIN | gebouw_id={args.gebouw_id} | scenario_id={args.scenario_id} | key={scenario.get('scenario_key')}")
    print("=" * 90)

    if missing:
        print("LET OP: option_ids niet gevonden in materials.jsonl:")
        for oid in missing:
            print("  -", oid)
        print("-" * 90)

    total_cost = 0.0
    total_mg = 0.0

    # header
    print(f"{'DRONE':10} {'ENH':4} {'QTY':>10} {'PRIJS':>10} {'COST':>12} {'CO2/u':>10} {'CO2':>12}  NAAM")
    print("-" * 90)

    for oid, m in chosen:
        drone = str(m.get("input_dronescan", "")).strip().upper()
        enh = str(m.get("enh", "")).strip()
        naam = str(m.get("naam", "")).strip()

        q, qsrc = qty_and_source(building, m)
        prijs = fnum(m.get("prijs_norm"), 0.0)
        cost = prijs * q

        co2u, co2src = mg_per_unit(m)
        co2 = co2u * q

        total_cost += cost
        total_mg += co2

        print(f"{drone:10} {enh:4} {q:10.2f} {prijs:10.2f} {cost:12.2f} {co2u:10.4f} {co2:12.4f}  {naam}")
        print(f"{'':10} {'':4} {'':>10} {'':>10} {'':>12} {'':>10} {'':>12}  qty_source={qsrc}, co2_source={co2src}, categorie={m.get('categorie')}")
        # waarschuwing als qty=0 voor m2/m1/deur
        if q == 0.0 and enh in ("m2", "m1") or (enh == "stuk" and drone == "DEUR"):
            print(f"{'':10} {'':4} {'':>10} {'':>10} {'':>12} {'':>10} {'':>12}  WARNING: qty=0 → check gebouwkolom ({qsrc})")
        print("-" * 90)

    print(f"TOTAAL COST: {total_cost:.2f}")
    print(f"TOTAAL CO2 : {total_mg:.4f}")
    print("=" * 90)


if __name__ == "__main__":
    main()
