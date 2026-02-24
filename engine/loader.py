# engine/loader.py

import json
from pathlib import Path
from typing import Dict, Any, Generator


def read_jsonl(path: Path) -> Generator[Dict[str, Any], None, None]:
    if not path.exists():
        raise FileNotFoundError(f"Bestand niet gevonden: {path}")

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_materials_lookup(path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Maakt een lookup:
      { material_id: { prijs, mg_co2_m2, mg_co2_stuk, enh } }
    """
    lookup: Dict[str, Dict[str, Any]] = {}

    for m in read_jsonl(path):
        material_id = m.get("material_id")
        if not material_id:
            continue

        lookup[material_id] = {
            "prijs": float(m.get("prijs_norm") or 0.0),
            "mg_co2_m2": float(m.get("mg_co2_m2") or 0.0),
            "mg_co2_stuk": float(m.get("mg_co2_stuk") or 0.0),
            "enh": (m.get("enh") or "").lower().strip(),
        }

    return lookup


def read_gebouw(path: Path, gebouw_id: int) -> Dict[str, Any] | None:
    """
    Leest gebouwgegevens.jsonl en retourneert het juiste gebouw record.
    Verwacht structuur zoals:
      {"gebouw_id":1,"01_m2":22.4,"04_stuks":2,...}
    """
    for g in read_jsonl(path):
        if g.get("gebouw_id") == gebouw_id:
            return g
    return None
