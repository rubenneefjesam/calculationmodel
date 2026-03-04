# utils/charts.py

import plotly.express as px
import plotly.graph_objects as go

DARK_BG     = "#0f1117"
CARD_BG     = "#1a1d27"
BORDER      = "#2a2d3a"
TEXT        = "#e5e7eb"
MUTED       = "#6b7280"


def bar_prijs(materialen: list) -> go.Figure:
    cats  = [m["categorie"] for m in materialen]
    vals  = [m["prijs"]     for m in materialen]
    fig = px.bar(
        x=cats, y=vals,
        labels={"x": "Onderdeel", "y": "Prijs (€)"},
        color=vals,
        color_continuous_scale="Oranges",
        title="Prijs per onderdeel",
    )
    fig.update_layout(
        paper_bgcolor=DARK_BG, plot_bgcolor=CARD_BG, font_color=TEXT,
        showlegend=False, coloraxis_showscale=False,
        height=260, margin=dict(t=40, b=20),
        xaxis=dict(gridcolor=BORDER), yaxis=dict(gridcolor=BORDER),
    )
    return fig


def bar_co2(materialen: list) -> go.Figure:
    cats = [m["categorie"] for m in materialen]
    vals = [m["co2"]       for m in materialen]
    fig = px.bar(
        x=cats, y=vals,
        labels={"x": "Onderdeel", "y": "CO₂ (kg)"},
        color=vals,
        color_continuous_scale="Blues",
        title="CO₂ per onderdeel",
    )
    fig.update_layout(
        paper_bgcolor=DARK_BG, plot_bgcolor=CARD_BG, font_color=TEXT,
        showlegend=False, coloraxis_showscale=False,
        height=260, margin=dict(t=40, b=20),
        xaxis=dict(gridcolor=BORDER), yaxis=dict(gridcolor=BORDER),
    )
    return fig


def radar(materialen: list) -> go.Figure | None:
    if not materialen:
        return None
    cats   = [m["categorie"] for m in materialen]
    p_max  = max(m["prijs"] for m in materialen) or 1
    c_max  = max(m["co2"]   for m in materialen) or 1
    p_norm = [round(m["prijs"] / p_max * 100, 1) for m in materialen]
    c_norm = [round(m["co2"]   / c_max * 100, 1) for m in materialen]
    d_norm = [m["duurzaam"] * 100                 for m in materialen]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=p_norm + [p_norm[0]], theta=cats + [cats[0]], name="Prijs",     fill="toself", line_color="#f97316"))
    fig.add_trace(go.Scatterpolar(r=c_norm + [c_norm[0]], theta=cats + [cats[0]], name="CO₂",      fill="toself", line_color="#60a5fa"))
    fig.add_trace(go.Scatterpolar(r=d_norm + [d_norm[0]], theta=cats + [cats[0]], name="Duurzaam",  fill="toself", line_color="#4ade80"))
    fig.update_layout(
        polar=dict(
            bgcolor=CARD_BG,
            radialaxis=dict(visible=True, range=[0, 100], color=MUTED),
            angularaxis=dict(color="#9ca3af"),
        ),
        paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG, font_color=TEXT,
        legend=dict(bgcolor=CARD_BG, bordercolor=BORDER),
        margin=dict(l=40, r=40, t=40, b=40), height=380,
    )
    return fig


def scatter_prijs_co2(df, top_ids: set) -> go.Figure:
    import pandas as pd
    df = df.copy()
    df["type"] = df["scenario_id"].apply(lambda x: "Top Optimaal" if x in top_ids else "Overig")

    fig = px.scatter(
        df,
        x="cost_total",
        y="co2_total",
        color="type",
        color_discrete_map={"Top Optimaal": "#4ade80", "Overig": "#374151"},
        opacity=0.6,
        labels={"cost_total": "Prijs (€)", "co2_total": "CO₂ (kg)", "type": ""},
        hover_data={"scenario_id": True, "cost_total": ":.0f", "co2_total": ":.0f", "type": False},
        title="Prijs vs CO₂ — alle scenario's",
    )
    fig.update_traces(marker=dict(size=4),                      selector=dict(name="Overig"))
    fig.update_traces(marker=dict(size=9, symbol="star"),        selector=dict(name="Top Optimaal"))
    fig.update_layout(
        paper_bgcolor=DARK_BG, plot_bgcolor=CARD_BG, font_color=TEXT,
        legend=dict(bgcolor=CARD_BG, bordercolor=BORDER),
        height=600,
        xaxis=dict(gridcolor=BORDER),
        yaxis=dict(gridcolor=BORDER),
    )
    return fig