# streamlit_app.py
#
# Hoofdbestand — navigatie, data laden, sidebar filters
# Draai met: streamlit run streamlit/streamlit_app.py
#

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from utils.data    import load_results, load_scenarios, load_materials, load_onderdelen, load_gebouw
from utils.helpers import format_eur, format_co2
from pages         import rankings, scatter, vergelijk

st.set_page_config(
    page_title="Gebouw Scenario Analyse",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Mono', monospace !important; letter-spacing: -0.02em; }
</style>
""", unsafe_allow_html=True)


# ── Data laden ───────────────────────────────────────────────────────────────
df_results = load_results()
keuzes_map = load_scenarios()
mat_lookup = load_materials()
ond_lookup = load_onderdelen()
gebouw     = load_gebouw()
afm        = gebouw.get("afmetingen", {})
gebouw_id  = gebouw.get("gebouw_id", "onbekend")

prijs_min = float(df_results["cost_total"].min())
prijs_max = float(df_results["cost_total"].max())
co2_min   = float(df_results["co2_total"].min())
co2_max   = float(df_results["co2_total"].max())


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 🏗️ {gebouw_id}")
    st.caption(f"{len(df_results):,} scenario's geanalyseerd")
    st.divider()

    pagina = st.radio(
        "Pagina",
        ["📊 Rankings", "🌐 Scatter", "⚖️ Vergelijk"],
        label_visibility="collapsed",
    )
    st.divider()

    st.markdown("**Filter**")
    max_prijs = st.slider("Max prijs (€)", int(prijs_min), int(prijs_max), int(prijs_max), step=1000, format="€%d")
    max_co2   = st.slider("Max CO₂ (kg)",  int(co2_min),  int(co2_max),  int(co2_max),  step=500,  format="%d kg")

    if pagina == "📊 Rankings":
        st.divider()
        st.markdown("**Ranking type**")
        ranking_keuze = st.radio(
            "",
            ["Optimaal", "Goedkoopste", "Duurste", "Minste CO₂", "Meeste CO₂"],
            label_visibility="collapsed",
        )
        top_n = st.select_slider("Top N", options=[10, 20, 50, 100], value=20)


# ── Pagina routing ───────────────────────────────────────────────────────────
if pagina == "📊 Rankings":
    rankings.render(
        df_results, keuzes_map, mat_lookup, ond_lookup, afm,
        max_prijs, max_co2, ranking_keuze, top_n,
    )

elif pagina == "🌐 Scatter":
    scatter.render(df_results, max_prijs, max_co2)

elif pagina == "⚖️ Vergelijk":
    vergelijk.render(
        df_results, keuzes_map, mat_lookup, ond_lookup, afm,
        max_prijs, max_co2,
    )