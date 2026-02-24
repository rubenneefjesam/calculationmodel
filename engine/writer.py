import json
from pathlib import Path


def write_summary(output_path: Path, result: dict):
    """
    Schrijft de samenvatting (decision output).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f_out:
        json.dump(result, f_out, indent=2, ensure_ascii=False)


def append_scenario_jsonl(output_path: Path, record: dict):
    """
    Schrijft één scenario-resultaat naar JSONL (append).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as f_out:
        f_out.write(json.dumps(record, ensure_ascii=False) + "\n")