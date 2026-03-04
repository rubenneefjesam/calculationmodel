# engine/calculator.py
from __future__ import annotations
from typing import Any, Dict

PANEEL_M2_PER_STUK = 1.7

# Mapping onderdeel_id -> (veld in afmetingen, enh)
ONDERDEEL_FACTOR_MAP: Dict[str, tuple] = {
    "01": ("beglazing_m2",  "m2"),
    "03": ("deuren_stuks",  "stuks"),
    "04": ("gevel_m2",      "m2"),
    "05": ("dak_m2",        "m2"),
    "06": ("kozijnen_m1",   "m1"),
    "07": ("dak_m2",        "stuks"),   # panelen: dak_m2 / PANEEL_M2_PER_STUK
    "08": ("dak_m2",        "m2"),
    "09": (None,            "stuks"),   # stadsverwarming: 1 stuk
    "10": (None,            "stuks"),   # ventilatie: 1 stuk
    "11": (None,            "stuks"),   # verwarming ketel: 1 stuk
    "12": (None,            "stuks"),   # verwarming warmtepomp: 1 stuk
    "13": ("vloer_m2",      "m2"),
    "14": ("dak_m2",        "stuks"),   # zonnepanelen: dak_m2 / PANEEL_M2_PER_STUK
}


def bepaal_factor(onderdeel_id: str, gebouw: Dict[str, Any]) -> float:
    """Bepaal de vermenigvuldigingsfactor op basis van onderdeel_id en gebouwafmetingen."""
    oid  = str(onderdeel_id).strip()
    afm  = gebouw.get("afmetingen", {})
    info = ONDERDEEL_FACTOR_MAP.get(oid)

    if info is None:
        return 0.0

    veld, enh = info

    if veld is None:
        return 1.0

    waarde = afm.get(veld)
    if waarde is None:
        return 0.0

    # Panelen en zonnepanelen: dakoppervlak / m2 per stuk
    if oid in ("07", "14"):
        return round(float(waarde) / PANEEL_M2_PER_STUK, 4)

    return float(waarde)


def bereken_totaal_prijs(
    keuzes: Dict[str, str],
    material_lookup: Dict[str, Dict[str, Any]],
    gebouw: Dict[str, Any],
) -> float:
    totaal = 0.0
    for onderdeel_id, material_id in keuzes.items():
        if material_id == "NONE":
            continue
        m = material_lookup.get(material_id)
        if not m:
            continue
        factor = bepaal_factor(onderdeel_id, gebouw)
        totaal += m["prijs"] * factor
    return round(totaal, 2)


def bereken_totaal_co2(
    keuzes: Dict[str, str],
    material_lookup: Dict[str, Dict[str, Any]],
    gebouw: Dict[str, Any],
) -> float:
    totaal = 0.0
    for onderdeel_id, material_id in keuzes.items():
        if material_id == "NONE":
            continue
        m = material_lookup.get(material_id)
        if not m:
            continue
        factor = bepaal_factor(onderdeel_id, gebouw)
        totaal += m["co2_value"] * factor
    return round(totaal, 2)