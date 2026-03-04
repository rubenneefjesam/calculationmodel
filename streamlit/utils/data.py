# utils/data.py

import json
import streamlit as st
import pandas as pd
from pathlib import Path


def get_root() -> Path:
    # streamlit/ map zit in de project root
    return Path(__file__).resolve().parents[2]


def find_file(pattern: str) -> Path:
    root = get_root()
    matches = sorted((root / "data/output").glob(pattern))
    if not matches:
        st.error(f"Geen bestand gevonden: data/output/{pattern}")
        st.stop()
    return matches[0]


@st.cache_data
def load_results() -> pd.DataFrame:
    path = find_file("results_gebouw_*.jsonl")
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    df = pd.DataFrame(rows)

    # Optimaal score berekenen
    p_min, p_max = df["cost_total"].min(), df["cost_total"].max()
    c_min, c_max = df["co2_total"].min(),  df["co2_total"].max()
    p_range = p_max - p_min or 1
    c_range = c_max - c_min or 1
    df["optimaal_score"] = (
        (df["cost_total"] - p_min) / p_range +
        (df["co2_total"]  - c_min) / c_range
    ) / 2

    return df


@st.cache_data
def load_scenarios() -> dict:
    path = get_root() / "data/output/scenarios.jsonl"
    if not path.exists():
        return {}
    lookup = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line)
            lookup[s["scenario_id"]] = s["keuzes"]
    return lookup


@st.cache_data
def load_materials() -> dict:
    path = get_root() / "data/brondata/materials.jsonl"
    return {
        m["material_id"]: m
        for m in [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    }


@st.cache_data
def load_onderdelen() -> dict:
    path = get_root() / "data/brondata/onderdelen.jsonl"
    return {
        o["onderdeel_id"]: o["categorie"]
        for o in [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    }


@st.cache_data
def load_gebouw() -> dict:
    path = get_root() / "data/gebouwdata/gebouwgegevens.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data[0] if isinstance(data, list) else data