"""Premier League data study — Streamlit dashboard.

Reads clean_data/ (via scripts/data_utils.py). Run from the repo root:
    env -u PYTHONPATH .venv/bin/streamlit run app.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "scripts"))
from data_utils import head_to_head, league_table, load_matches, team_form, to_team_matches  # noqa: E402

# Colors from the project's validated palette (dataviz skill, references/palette.md)
BLUE, RED, GRAY = "#2a78d6", "#e34948", "#9a988f"
plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e5e4e0", "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

st.set_page_config(page_title="Premier League Data Study", layout="wide")


@st.cache_data
def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    matches = load_matches()
    return matches, to_team_matches(matches)


matches, team_matches = get_data()
seasons = sorted(matches["season"].unique())
teams = sorted(matches["home_team"].unique())

st.title("Premier League Data Study")
st.caption(
    f"{len(matches):,} played matches, {seasons[0]} to {seasons[-1]}. "
    "Built from `clean_data/matches.csv` — match identity and full-time score only "
    "(fields available in every season). See `clean_data/README.md` for what's excluded and why."
)

tab_table, tab_form, tab_h2h = st.tabs(["League table", "Team form", "Head-to-head"])

# --------------------------------------------------------------------------- League table
with tab_table:
    season = st.selectbox("Season", seasons, index=len(seasons) - 1, key="table_season")
    table = league_table(team_matches, season)

    expected_teams = table["played"].mode().iloc[0] + 1  # e.g. 38 played -> 20 teams
    if table["played"].nunique() > 1 or (table["played"] != expected_teams - 1).any():
        st.info(
            f"{season} is not a complete season in the data — teams have played different "
            "numbers of matches, so this table is a partial, in-progress standing."
        )

    display = table.rename(columns={
        "team": "Team", "played": "P", "wins": "W", "draws": "D", "losses": "L",
        "goals_for": "GF", "goals_against": "GA", "goal_diff": "GD", "points": "Pts",
    })[["Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]]
    st.dataframe(display, use_container_width=True, height=min(38 + 35 * len(display), 800))

    fig, ax = plt.subplots(figsize=(8, 0.35 * len(table) + 1))
    y = range(len(table), 0, -1)
    ax.barh(y, table["points"], color=BLUE, height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels(table["team"], fontsize=8)
    ax.set_xlabel("Points")
    ax.set_title(f"{season} table")
    for yi, pts in zip(y, table["points"]):
        ax.text(pts + 0.5, yi, str(pts), va="center", fontsize=7, color="#52514e")
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

# --------------------------------------------------------------------------- Team form
with tab_form:
    col1, col2 = st.columns(2)
    team = col1.selectbox("Team", teams, index=teams.index("Arsenal") if "Arsenal" in teams else 0)
    team_seasons = sorted(team_matches.loc[team_matches["team"] == team, "season"].unique())
    season = col2.selectbox("Season", team_seasons, index=len(team_seasons) - 1, key="form_season")
    window = st.slider("Rolling form window (matches)", min_value=3, max_value=10, value=5)

    form = team_form(team_matches, team, season, window=window)
    wins, draws, losses = (form["outcome"] == "W").sum(), (form["outcome"] == "D").sum(), (form["outcome"] == "L").sum()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Record", f"{wins}W {draws}D {losses}L")
    m2.metric("Points", int(form["points"].sum()))
    m3.metric("Goals for", int(form["goals_for"].sum()))
    m4.metric("Goals against", int(form["goals_against"].sum()))

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(form["matchday"], form["rolling_points"], color=BLUE, linewidth=2, marker="o", markersize=4)
    ax.set_xlabel("Matchday")
    ax.set_ylabel(f"Points, last {window} games")
    ax.set_ylim(0, window * 3 + 0.5)
    ax.set_title(f"{team} {season} — rolling {window}-game form")
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    st.dataframe(
        form.rename(columns={
            "matchday": "MD", "date": "Date", "opponent": "Opponent", "venue": "Venue",
            "goals_for": "GF", "goals_against": "GA", "outcome": "Result", "points": "Pts",
            "rolling_points": f"Last {window}", "cumulative_points": "Cum. Pts",
        }),
        use_container_width=True, hide_index=True,
    )

# --------------------------------------------------------------------------- Head-to-head
with tab_h2h:
    col1, col2 = st.columns(2)
    team_a = col1.selectbox("Team A", teams, index=teams.index("Arsenal") if "Arsenal" in teams else 0, key="h2h_a")
    team_b_options = [t for t in teams if t != team_a]
    default_b = "Tottenham Hotspur" if "Tottenham Hotspur" in team_b_options else team_b_options[0]
    team_b = col2.selectbox("Team B", team_b_options, index=team_b_options.index(default_b), key="h2h_b")

    try:
        summary, games = head_to_head(matches, team_a, team_b)
    except ValueError:
        st.warning(f"{team_a} and {team_b} have never played each other in this data.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Played", summary["played"])
        m2.metric(f"{team_a} wins", summary[f"{team_a}_wins"])
        m3.metric("Draws", summary["draws"])
        m4.metric(f"{team_b} wins", summary[f"{team_b}_wins"])

        fig, ax = plt.subplots(figsize=(8, 1.6))
        labels = [f"{team_a} wins", "Draws", f"{team_b} wins"]
        values = [summary[f"{team_a}_wins"], summary["draws"], summary[f"{team_b}_wins"]]
        colors = [BLUE, GRAY, RED]
        left = 0
        for label, value, color in zip(labels, values, colors):
            ax.barh(0, value, left=left, color=color, height=0.55)
            if value > 0:
                ax.text(left + value / 2, 0, str(value), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
            left += value
        ax.set_xlim(0, left)
        ax.set_yticks([])
        ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, frameon=False)
        ax.set_title(f"{team_a} vs {team_b}, all-time ({summary['played']} matches)")
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

        st.dataframe(
            games[["season", "date", "home_team", "away_team", "home_goals", "away_goals", "result"]]
            .rename(columns={
                "season": "Season", "date": "Date", "home_team": "Home", "away_team": "Away",
                "home_goals": "HG", "away_goals": "AG", "result": "Result",
            })
            .sort_values("Date", ascending=False),
            use_container_width=True, hide_index=True,
        )
