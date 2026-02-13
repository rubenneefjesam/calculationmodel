#!/usr/bin/env python3
# scripts/convert_csv_to_jsonl.py

import csv
import json
import re
import sys
from pathlib import Path

X_NULL_VALUES = {"", "x", "X", "-", "—", "n.v.t.", "nvt", "na", "null", "None"}

def snake_case(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[€]", " ", s)
    s = re.sub(r"[\s/]+", "_", s)
    s = re.sub(r"[-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "col"

_num_re = re.compile(r"^\s*-?\d+(?:[.,]\d+)?\s*$")

def parse_value(v: str):
    if v is None:
        return None
    v = v.strip()

    if v in X_NULL_VALUES:
        return None

    # verwijder rare encoding artifacts + euro
    # U+FFFD = replacement char "�"
    v_clean = (
        v.replace("\ufffd", "")   # �
         .replace("�", "")        # soms letterlijk
         .replace("€", "")        # euro
         .replace("Â", "")        # Excel/cp1252->utf8 artifact
         .replace("\u00a0", " ")  # nbsp
         .strip()
    )

    # getal detectie: 1.300 of 1 300 of 39,6 of " 15.000 "
    v_digits = v_clean.replace(" ", "")

    # als het exact op een nummer lijkt
    if _num_re.match(v_digits):
        # 1.300 kan NL duizendtallen zijn -> 1300 als er 3 cijfers na punt staan
        if "." in v_digits and "," not in v_digits:
            left, right = v_digits.split(".", 1)
            if right.isdigit() and len(right) == 3 and left.isdigit():
                v_digits = left + right

        # 39,6 -> 39.6
        v_digits = v_digits.replace(",", ".")
        try:
            f = float(v_digits)
            if f.is_integer():
                return int(f)
            return f
        except ValueError:
            pass

    return v_clean


def sniff_dialect(sample: str):
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t|")
    except Exception:
        class D:
            delimiter = ";"
        return D()


def read_text_with_fallback(csv_path: Path) -> str:
    """
    Probeer de meest voorkomende Excel encodings.
    We vermijden errors='replace' zodat € niet verandert in �.
    """
    data = csv_path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = data.decode(enc)
            # als je toch replacement chars ziet, probeer volgende encoding
            if "\ufffd" in text:
                continue
            return text
        except Exception:
            continue
    # laatste redmiddel: latin-1 (altijd decodebaar)
    return data.decode("latin-1")


def convert(csv_path: Path, jsonl_path: Path, normalize_headers: bool = True):
    text = read_text_with_fallback(csv_path)
    text = text.lstrip("\ufeff")

    sample = "\n".join(text.splitlines()[:20])
    dialect = sniff_dialect(sample)

    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    if not lines:
        raise SystemExit("CSV is leeg.")

    reader = csv.DictReader(lines, delimiter=dialect.delimiter)

    raw_headers = reader.fieldnames or []
    if normalize_headers:
        headers = [snake_case(h) for h in raw_headers]
        header_map = dict(zip(raw_headers, headers))
    else:
        header_map = {h: h for h in raw_headers}

    out_lines = 0
    with jsonl_path.open("w", encoding="utf-8") as f_out:
        for row in reader:
            obj = {}
            for k_raw, v in row.items():
                if k_raw is None:
                    continue
                k = header_map.get(k_raw, k_raw)
                obj[k] = parse_value(v)

            if all(v is None for v in obj.values()):
                continue

            f_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            out_lines += 1

    return out_lines, dialect.delimiter


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_csv_to_jsonl.py materials.csv [materials.jsonl]")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    jsonl_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else csv_path.with_suffix(".jsonl")

    if not csv_path.exists():
        raise SystemExit(f"Bestand niet gevonden: {csv_path}")

    out_lines, delim = convert(csv_path, jsonl_path, normalize_headers=True)
    print(f"OK: {csv_path} -> {jsonl_path} | rows={out_lines} | delimiter='{delim}'")

if __name__ == "__main__":
    main()
