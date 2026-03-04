# views/rankings.py

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.helpers import format_eur, format_co2, bereken_materialen, duurzaam_score, materialen_df_display
from utils.charts  import bar_prijs, bar_co2, radar


def render(df_results, keuzes_map, mat_lookup, ond_lookup, afm,
           max_prijs, max_co2, ranking_keuze, top_n):

    sort_map = {
        "Optimaal":    ("optimaal_score", False),
        "Goedkoopste": ("cost_total",     False),
        "Duurste":     ("cost_total",     True),
        "Minste CO₂":  ("co2_total",      False),
        "Meeste CO₂":  ("co2_total",      True),
    }

    df_filtered = df_results[
        (df_results["cost_total"] <= max_prijs) &
        (df_results["co2_total"]  <= max_co2)
    ]

    sort_col, sort_desc = sort_map[ranking_keuze]
    df_ranked = df_filtered.sort_values(sort_col, ascending=not sort_desc).head(top_n)

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"## Scenario Analyse — {ranking_keuze}")
    st.caption(f"{len(df_filtered):,} van {len(df_results):,} scenario's na filter — top {len(df_ranked)} getoond")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totaal",       f"{len(df_results):,}")
    c2.metric("Na filter",    f"{len(df_filtered):,}")
    c3.metric("Prijs range",  f"{format_eur(df_results['cost_total'].min())} – {format_eur(df_results['cost_total'].max())}")
    c4.metric("CO₂ range",    f"{format_co2(df_results['co2_total'].min())} – {format_co2(df_results['co2_total'].max())}")

    st.divider()

    col_lijst, col_detail = st.columns([1.2, 1], gap="large")

    # ── Lijst ────────────────────────────────────────────────────────────────
    with col_lijst:
        st.markdown(f"#### Top {len(df_ranked)} — {ranking_keuze}")

        if df_ranked.empty:
            st.warning("Geen scenario's voldoen aan de filters.")
            return

        display_df = pd.DataFrame({
            "#":        range(1, len(df_ranked) + 1),
            "Scenario": df_ranked["scenario_id"].values,
            "Prijs":    df_ranked["cost_total"].apply(format_eur).values,
            "CO₂":      df_ranked["co2_total"].apply(format_co2).values,
            "Score":    df_ranked["optimaal_score"].apply(lambda x: f"{x:.4f}").values,
        })

        sel      = st.dataframe(display_df, use_container_width=True, hide_index=True,
                                on_select="rerun", selection_mode="single-row", height=560)
        sel_rows = sel.selection.get("rows", [])
        sel_idx  = sel_rows[0] if sel_rows else 0
        selected_id = int(df_ranked.iloc[sel_idx]["scenario_id"])

    # ── Detail ───────────────────────────────────────────────────────────────
    with col_detail:
        row        = df_results[df_results["scenario_id"] == selected_id].iloc[0]
        materialen = bereken_materialen(selected_id, keuzes_map, mat_lookup, ond_lookup, afm)
        d_score    = duurzaam_score(materialen)

        st.markdown(f"#### Scenario #{selected_id}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Totale prijs",  format_eur(row["cost_total"]))
        m2.metric("Totale CO₂",   format_co2(row["co2_total"]))
        m3.metric("Duurzaamheid",  f"{d_score:.0f}%")

        tab1, tab2, tab3 = st.tabs(["📋 Materialen", "📈 Charts", "🕸️ Radar"])

        with tab1:
            st.dataframe(materialen_df_display(materialen), use_container_width=True, hide_index=True, height=350)

        with tab2:
            st.plotly_chart(bar_prijs(materialen), use_container_width=True)
            st.plotly_chart(bar_co2(materialen),   use_container_width=True)

        with tab3:
            fig = radar(materialen)
            if fig:
                st.plotly_chart(fig, use_container_width=True)