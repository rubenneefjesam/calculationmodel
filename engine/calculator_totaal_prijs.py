# engine/calculator_totaal_prijs.py

from __future__ import annotations

from typing import Dict, Any


def _norm_enh(enh: str | None) -> str:
    e = (enh or "").strip().lower()
    return "stuks" if e == "stuk" else e


def bepaal_factor(onderdeel_id: str, enh: str, gebouw: Dict[str, Any]) -> float:
    """
    Nieuwe logica: factor komt direct uit gebouwgegevens.jsonl via sleutel:
      "<onderdeel_id>_<enh>"
    Voorbeeld: onderdeel_id="01", enh="m2" -> key "01_m2"
    """
    oid = str(onderdeel_id).strip()
    e = _norm_enh(enh)

    if not oid or not e:
        return 0.0

    key = f"{oid}_{e}"

    try:
        return float(gebouw.get(key) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def bereken_totaal_prijs(
    keuzes: Dict[str, str],
    material_lookup: Dict[str, Dict[str, Any]],
    gebouw: Dict[str, Any],
) -> float:
    totaal = 0.0

    # LET OP: we gebruiken onderdeel_id uit scenario keys
    for onderdeel_id, material_id in keuzes.items():
        if material_id == "NONE":
            continue

        m = material_lookup.get(material_id)
        if not m:
            continue

        enh = _norm_enh(m.get("enh"))
        factor = bepaal_factor(onderdeel_id, enh, gebouw)

        totaal += float(m.get("prijs") or 0.0) * factor

    return round(totaal, 2)
