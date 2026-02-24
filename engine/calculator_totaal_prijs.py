from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Set


def _norm_enh(enh: str | None) -> str:
    e = (enh or "").strip().lower()
    if e == "stuk":
        return "stuks"
    return e


def _norm_categorie(cat: str | None) -> str:
    c = (cat or "").strip()

    # Alias voor bekende varianten
    aliases = {
        "Deur": "Deuren",
        "Kozijnen": "Kozijnen/Draaiend deel",
        "Vloerisolatie": "Bodem/Vloerisolatie",
    }
    return aliases.get(c, c)


def _cat_to_key_base(cat: str) -> str:
    """
    Converteer categorie naar sleutelbasis zoals in gebouwgegevens.jsonl:
    - spaties, '/', ',' -> '_'
    - meerdere underscores normaliseren
    Voorbeeld: "Bodem/Vloerisolatie" -> "Bodem_Vloerisolatie"
    """
    s = cat.strip()
    s = re.sub(r"[ /,]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s


def load_onderdelen_lookup(path: Path) -> Dict[str, Set[str]]:
    """
    Leest onderdelen.jsonl en maakt:
      { "Beglazing": {"m2"}, "Deuren": {"stuks"}, ... }
    """
    lookup: Dict[str, Set[str]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            o = json.loads(line)
            cat = (o.get("categorie") or "").strip()
            enh_list = o.get("enh") or []
            enh_set = {_norm_enh(x) for x in enh_list if str(x).strip()}
            if cat:
                lookup[cat] = enh_set
    return lookup


def bepaal_factor(
    materiaal: Dict[str, Any],
    gebouw: Dict[str, Any],
    onderdelen_lookup: Optional[Dict[str, Set[str]]] = None,
    strict_enh: bool = False,
) -> float:
    """
    Zoekt factor in gebouwgegevens.jsonl op basis van categorie + enh:
      key = "<CategorieKey>_<enhNorm>"
    Voorbeeld: Beglazing + m2 -> Beglazing_m2

    Als onderdelen_lookup is meegegeven:
      - checkt of materiaal.enh toegestaan is voor deze categorie.
      - strict_enh=True -> raise ValueError bij mismatch.
      - strict_enh=False -> probeert 'best effort' (bij 1 toegestane enh).
    """
    categorie = _norm_categorie(materiaal.get("categorie"))
    enh = _norm_enh(materiaal.get("enh"))

    if not categorie or not enh:
        return 0.0

    # Validatie t.o.v. onderdelen.jsonl
    if onderdelen_lookup is not None:
        allowed = onderdelen_lookup.get(categorie)
        if allowed:
            if enh not in allowed:
                if strict_enh:
                    raise ValueError(
                        f"enh-mismatch: categorie '{categorie}' verwacht {sorted(allowed)}, "
                        f"maar materiaal heeft enh='{enh}' (material_id={materiaal.get('material_id')})."
                    )
                # best effort: als er precies 1 toegestane enh is, gebruik die
                if len(allowed) == 1:
                    enh = next(iter(allowed))

    key_base = _cat_to_key_base(categorie)
    key = f"{key_base}_{enh}"

    val = gebouw.get(key)

    # Legacy fallback (alleen handig zolang niet alle gebouwdata is omgezet)
    if val is None:
        legacy = {
            "Beglazing_m2": "VASTGLAS_m2",
            "Gevelisolatie_m2": "METSELWERK_m2",
            "Plat_dakisolatie_m2": "DAKOPPERVLAK_m2",
            "Hellend_dakisolatie_m2": "DAKOPPERVLAK_m2",
            "Bodem_Vloerisolatie_m2": "VLOER_BODEM_m2",
            "Deuren_stuks": "DEUR_stuks",
            "Kozijnen_Draaiend_deel_m1": "KOZIJNEN_m1",
            "Kozijnen_m1": "KOZIJNEN_m1",
        }
        legacy_key = legacy.get(key)
        if legacy_key:
            val = gebouw.get(legacy_key)

    try:
        return float(val or 0.0)
    except (TypeError, ValueError):
        return 0.0


def bereken_totaal_prijs(
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

        factor = bepaal_factor(m, gebouw, onderdelen_lookup=onderdelen_lookup, strict_enh=False)
        totaal += float(m.get("prijs") or 0.0) * factor

    return round(totaal, 2)
