import json
from pathlib import Path


def load_requirements(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Requirements bestand niet gevonden: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def voldoet_aan_constraints(record, constraints: dict):
    """
    record bevat:
        {
            "totaal_prijs": ...,
            "totaal_co2": ...
        }
    """

    for veld, regels in constraints.items():
        waarde = record.get(veld)

        if waarde is None:
            return False

        min_val = regels.get("min")
        max_val = regels.get("max")

        if min_val is not None and waarde < min_val:
            return False

        if max_val is not None and waarde > max_val:
            return False

    return True