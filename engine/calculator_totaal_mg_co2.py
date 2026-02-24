# engine/calculator_totaal_mg_co2.py

from __future__ import annotations

from typing import Dict, Any

from engine.calculator_totaal_prijs import bepaal_factor, _norm_enh


def bereken_totaal_mg_co2(
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

        # co2 veld kiezen op basis van enh
        if enh == "stuks":
            totaal += float(m.get("mg_co2_stuk") or 0.0) * factor
        else:
            totaal += float(m.get("mg_co2_m2") or 0.0) * factor

    return round(totaal, 2)
