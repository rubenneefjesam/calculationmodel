import json


def write_results(output_path, gebouw_id, scenario_count,
                  goedkoopste, duurste, laagste_co2):

    result = {
        "meta": {
            "gebouw_id": gebouw_id,
            "scenarios_evaluated": scenario_count
        },
        "goedkoopste_10": goedkoopste,
        "duurste_10": duurste,
        "laagste_co2_10": laagste_co2
    }

    with output_path.open("w", encoding="utf-8") as f_out:
        json.dump(result, f_out, indent=2, ensure_ascii=False)