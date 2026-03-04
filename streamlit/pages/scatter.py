# pages/scatter.py

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.helpers import format_eur, format_co2
from utils.charts  import scatter_prijs_co2


def render(df_results, max_prijs, max_co2):

    st.markdown("## Prijs vs CO₂ — Alle scenario's")

    # Top 20 optimaal highlighten
    top_ids = set(
        df_results.sort_values("optimaal_score").head(20)["scenario_id"].values
    )

    df_filtered = df_results[
        (df_results["cost_total"] <= max_prijs) &
        (df_results["co2_total"]  <= max_co2)
    ]

    st.caption(f"{len(df_filtered):,} van {len(df_results):,} scenario's zichtbaar")

    fig = scatter_prijs_co2(df_filtered, top_ids)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Laagste prijs",    format_eur(df_filtered["cost_total"].min()))
    c2.metric("Laagste CO₂",      format_co2(df_filtered["co2_total"].min()))
    c3.metric("Zichtbare punten", f"{len(df_filtered):,}")