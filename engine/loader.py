import json
from pathlib import Path


def read_jsonl(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Bestand niet gevonden: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def read_materials_lookup(path: Path):
    lookup = {}

    for m in read_jsonl(path):
        material_id = m.get("material_id")
        if not material_id:
            continue

        lookup[material_id] = {
            "prijs": float(m.get("prijs_norm") or 0),
            "co2": float(m.get("mg_co2_m2") or 0),
            "categorie": m.get("categorie"),
            "enh": (m.get("enh") or "").lower()
        }

    return lookup


def read_gebouw(path: Path, gebouw_id: int):
    for g in read_jsonl(path):
        if g.get("gebouw_id") == gebouw_id:
            return g
    return None