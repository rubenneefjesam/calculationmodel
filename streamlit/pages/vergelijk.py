# pages/vergelijk.py

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.helpers import format_eur, format_co2, bereken_materialen, duurzaam_score
from utils.charts  import radar


def render(df_results, keuzes_map, mat_lookup, ond_lookup, afm, max_prijs, max_co2):

    st.markdown("## Scenario Vergelijking")

    df_filtered = df_results[
        (df_results["cost_total"] <= max_prijs) &
        (df_results["co2_total"]  <= max_co2)
    ].sort_values("optimaal_score").head(200)

    if len(df_filtered) < 2:
        st.warning("Pas de filters aan om meer scenario's te tonen.")
        return

    opties = {
        f"#{int(r['scenario_id'])} — {format_eur(r['cost_total'])} | CO₂: {format_co2(r['co2_total'])}": int(r["scenario_id"])
        for _, r in df_filtered.iterrows()
    }
    optie_labels = list(opties.keys())

    col_a, col_b = st.columns(2)
    with col_a:
        keuze_a = st.selectbox("Scenario A", optie_labels, index=0, key="verg_a")
    with col_b:
        keuze_b = st.selectbox("Scenario B", optie_labels, index=min(1, len(optie_labels) - 1), key="verg_b")

    id_a = opties[keuze_a]
    id_b = opties[keuze_b]

    row_a = df_results[df_results["scenario_id"] == id_a].iloc[0]
    row_b = df_results[df_results["scenario_id"] == id_b].iloc[0]
    mat_a = bereken_materialen(id_a, keuzes_map, mat_lookup, ond_lookup, afm)
    mat_b = bereken_materialen(id_b, keuzes_map, mat_lookup, ond_lookup, afm)

    # ── Totalen ──────────────────────────────────────────────────────────────
    st.divider()
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("A — Prijs",     format_eur(row_a["cost_total"]))
    m2.metric("B — Prijs",     format_eur(row_b["cost_total"]),
              delta=f"€ {row_b['cost_total'] - row_a['cost_total']:+,.0f}", delta_color="inverse")
    m3.metric("A — CO₂",       format_co2(row_a["co2_total"]))
    m4.metric("B — CO₂",       format_co2(row_b["co2_total"]),
              delta=f"{row_b['co2_total'] - row_a['co2_total']:+,.0f} kg", delta_color="inverse")
    m5.metric("A — Duurzaam",  f"{duurzaam_score(mat_a):.0f}%")
    m6.metric("B — Duurzaam",  f"{duurzaam_score(mat_b):.0f}%",
              delta=f"{duurzaam_score(mat_b) - duurzaam_score(mat_a):+.0f}%")

    # ── Per-onderdeel tabel ───────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Vergelijking per onderdeel")

    dict_a = {m["categorie"]: m for m in mat_a}
    dict_b = {m["categorie"]: m for m in mat_b}
    alle_cats = sorted(set(list(dict_a.keys()) + list(dict_b.keys())))

    rows = []
    for cat in alle_cats:
        a = dict_a.get(cat, {})
        b = dict_b.get(cat, {})
        rows.append({
            "Onderdeel":     cat,
            "A — Materiaal": a.get("naam", "-"),
            "B — Materiaal": b.get("naam", "-"),
            "Zelfde":        "✓" if a.get("naam") == b.get("naam") else "✗",
            "Prijs A":       f"€ {a.get('prijs', 0):,.0f}",
            "Prijs B":       f"€ {b.get('prijs', 0):,.0f}",
            "Prijs Δ":       f"{b.get('prijs', 0) - a.get('prijs', 0):+,.0f}",
            "CO₂ A":         f"{a.get('co2', 0):,.0f} kg",
            "CO₂ B":         f"{b.get('co2', 0):,.0f} kg",
            "CO₂ Δ":         f"{b.get('co2', 0) - a.get('co2', 0):+,.0f} kg",
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Radar charts naast elkaar ─────────────────────────────────────────────
    st.divider()
    st.markdown("#### Radar vergelijking")
    rc1, rc2 = st.columns(2)
    with rc1:
        st.caption(f"Scenario #{id_a}")
        fig_a = radar(mat_a)
        if fig_a:
            st.plotly_chart(fig_a, use_container_width=True)
    with rc2:
        st.caption(f"Scenario #{id_b}")
        fig_b = radar(mat_b)
        if fig_b:
            st.plotly_chart(fig_b, use_container_width=True)