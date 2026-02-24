def bepaal_factor(materiaal, gebouw):
    categorie = materiaal["categorie"]

    mapping = {
        "Beglazing": "VASTGLAS_m2",
        "Gevelisolatie": "METSELWERK_m2",
        "Plat dakisolatie": "DAKOPPERVLAK_m2",
        "Hellend dakisolatie": "DAKOPPERVLAK_m2",
        "Vloerisolatie": "VLOER_BODEM_m2",
        "Deur": "DEUR_stuks",
        "Kozijnen": "KOZIJNEN_m1"
    }

    veld = mapping.get(categorie)

    if veld and veld in gebouw:
        return float(gebouw.get(veld) or 0)

    return 1.0


def bereken_scenario(keuzes, material_lookup, gebouw):
    totaal_prijs = 0.0
    totaal_co2 = 0.0

    for material_id in keuzes.values():
        if material_id == "NONE":
            continue

        m = material_lookup.get(material_id)
        if not m:
            continue

        factor = bepaal_factor(m, gebouw)

        totaal_prijs += m["prijs"] * factor
        totaal_co2 += m["co2"] * factor

    return round(totaal_prijs, 2), round(totaal_co2, 2)