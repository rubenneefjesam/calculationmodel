# engine/loader.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Generator, Optional


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
    Lookup: { material_id -> { prijs, co2_value, enh, naam, duurzaam } }
    Veldnamen conform nieuwe materials.jsonl (gen_csv.py output).
    """
    lookup: Dict[str, Dict[str, Any]] = {}
    for m in read_jsonl(path):
        mid = m.get("material_id")
        if not mid:
            continue
        lookup[mid] = {
            "prijs":      float(m.get("prijs")     or 0.0),
            "co2_value":  float(m.get("co2_value") or 0.0),
            "enh":        (m.get("enh") or "").lower().strip(),
            "naam":       m.get("naam"),
            "duurzaam":   m.get("duurzaam"),
            "onderdeel_id": m.get("onderdeel_id"),
        }
    return lookup


def read_gebouw(path: Path, gebouw_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Leest gebouwgegevens.json (nieuw formaat met afmetingen + opties).
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        if gebouw_id:
            for g in data:
                if str(g.get("gebouw_id")) == str(gebouw_id):
                    return g
        return data[0] if data else None
    return data