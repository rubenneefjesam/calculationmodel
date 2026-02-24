from __future__ import annotations

from typing import Dict, Any, Optional, Set

from engine.calculator_totaal_prijs import bepaal_factor, _norm_enh


def bereken_totaal_mg_co2(
    keuzes: Dict[str, str],
    material_lookup: Dict[str, Dict[str, Any]],
    gebouw: Dict[str, Any],
    onderdelen_lookup: Optional[Dict[str, Set[str]]] = None,
) -> float:
    totaal = 0.0

    for material_id in keuzes.values():
        if material_id == "NONE":
            continue

        m = material_lookup.get(material_id)
        if not m:
            continue

        enh = _norm_enh(m.get("enh"))
        factor = bepaal_factor(m, gebouw, onderdelen_lookup=onderdelen_lookup, strict_enh=False)

        # co2 veld kiezen op basis van enh
        if enh in ("stuks", "stuk"):
            totaal += float(m.get("mg_co2_stuk") or 0.0) * factor
        else:
            totaal += float(m.get("mg_co2_m2") or 0.0) * factor

    return round(totaal, 2)
