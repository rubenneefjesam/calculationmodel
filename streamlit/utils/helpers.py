# utils/helpers.py

PANEEL_M2_PER_STUK = 1.7

VELD_MAP = {
    "01": ("beglazing_m2",  "m2"),
    "03": ("deuren_stuks",  "stuks"),
    "04": ("gevel_m2",      "m2"),
    "05": ("dak_m2",        "m2"),
    "06": ("kozijnen_m1",   "m1"),
    "07": ("dak_m2",        "stuks"),
    "08": ("dak_m2",        "m2"),
    "09": (None,            "stuks"),
    "10": (None,            "stuks"),
    "11": (None,            "stuks"),
    "12": (None,            "stuks"),
    "13": ("vloer_m2",      "m2"),
    "14": ("dak_m2",        "stuks"),
}


def format_eur(val: float) -> str:
    return f"€ {val:,.0f}".replace(",", ".")


def format_co2(val: float) -> str:
    return f"{val:,.0f} kg".replace(",", ".")


def bereken_materialen(scenario_id: int, keuzes_map: dict, mat_lookup: dict, ond_lookup: dict, afm: dict) -> list:
    keuzes = keuzes_map.get(scenario_id, {})
    materialen = []
    for oid, mid in keuzes.items():
        m = mat_lookup.get(mid, {})
        veld, enh = VELD_MAP.get(oid, (None, ""))
        if veld is None:
            waarde = 1.0
        elif oid in ("07", "14"):
            waarde = round(float(afm.get(veld, 0)) / PANEEL_M2_PER_STUK, 2)
        else:
            waarde = float(afm.get(veld, 0))
        materialen.append({
            "onderdeel_id": oid,
            "categorie":    ond_lookup.get(oid, oid),
            "naam":         m.get("naam", "-"),
            "waarde":       waarde,
            "enh":          enh,
            "prijs":        round(float(m.get("prijs") or 0) * waarde, 2),
            "co2":          round(float(m.get("co2_value") or 0) * waarde, 2),
            "duurzaam":     int(m.get("duurzaam") or 0),
        })
    return materialen


def duurzaam_score(materialen: list) -> float:
    if not materialen:
        return 0.0
    return round(sum(1 for m in materialen if m["duurzaam"]) / len(materialen) * 100, 1)


def materialen_df_display(materialen: list):
    import pandas as pd
    return pd.DataFrame([{
        "Onderdeel": m["categorie"],
        "Materiaal": m["naam"],
        "Waarde":    f"{m['waarde']:,.1f} {m['enh']}",
        "Prijs":     f"€ {m['prijs']:,.2f}",
        "CO₂":       f"{m['co2']:,.2f} kg",
        "Duurzaam":  "✓" if m["duurzaam"] else "✗",
    } for m in materialen])