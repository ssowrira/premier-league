"""Shared data-access and analysis helpers for the Premier League data study.

Imported by app.py and by notebooks (after adding scripts/ to sys.path — see
notebooks/AGENTS.md). Every function here was prototyped and tested in
notebooks/04_utility_functions.ipynb; keep that notebook's function bodies and
this file in sync if either changes.

Typical use:
    matches = load_matches()
    team_matches = to_team_matches(matches)
    table = league_table(team_matches, "2003-04")
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN_DATA = ROOT / "clean_data"


def load_matches(clean_data_dir: Path = CLEAN_DATA) -> pd.DataFrame:
    """Load the clean match-grain table (clean_data/matches.csv).

    One row per played match, 1992-93 onwards. See clean_data/README.md for the
    column dictionary and which seasons are complete.
    """
    df = pd.read_csv(clean_data_dir / "matches.csv", parse_dates=["date"])
    return df.sort_values(["date", "home_team"]).reset_index(drop=True)


def to_team_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Reshape match-grain rows into team-grain rows (two per match: home and away).

    Adds, from each team's perspective: venue, opponent, goals_for/against,
    goal_diff, outcome (W/D/L) and points (3/1/0).
    """
    sides = []
    for venue, own, opp in [("Home", "home", "away"), ("Away", "away", "home")]:
        side = matches.rename(columns={
            f"{own}_team": "team", f"{own}_team_code": "team_code",
            f"{opp}_team": "opponent", f"{opp}_team_code": "opponent_code",
            f"{own}_goals": "goals_for", f"{opp}_goals": "goals_against",
        })[["match_id", "season", "season_start_year", "date", "day_of_week",
            "team", "team_code", "opponent", "opponent_code", "goals_for", "goals_against"]].copy()
        side["venue"] = venue
        win_result = "H" if venue == "Home" else "A"
        loss_result = "A" if venue == "Home" else "H"
        side["outcome"] = matches["result"].map({win_result: "W", "D": "D", loss_result: "L"})
        sides.append(side)

    team_matches = pd.concat(sides, ignore_index=True)
    team_matches["goal_diff"] = team_matches["goals_for"] - team_matches["goals_against"]
    team_matches["points"] = team_matches["outcome"].map({"W": 3, "D": 1, "L": 0})
    return team_matches.sort_values(["date", "team"]).reset_index(drop=True)


def league_table(team_matches: pd.DataFrame, season: str) -> pd.DataFrame:
    """Final (or current) standings for one season.

    Ranked by points, then goal difference, then goals scored — the Premier
    League tiebreak order.
    """
    season_matches = team_matches[team_matches["season"] == season]
    if season_matches.empty:
        raise ValueError(f"no matches found for season {season!r}")

    table = season_matches.groupby("team").agg(
        played=("match_id", "size"),
        wins=("outcome", lambda s: (s == "W").sum()),
        draws=("outcome", lambda s: (s == "D").sum()),
        losses=("outcome", lambda s: (s == "L").sum()),
        goals_for=("goals_for", "sum"),
        goals_against=("goals_against", "sum"),
        points=("points", "sum"),
    )
    table["goal_diff"] = table["goals_for"] - table["goals_against"]
    table = table.sort_values(["points", "goal_diff", "goals_for"], ascending=False).reset_index()
    table.index = table.index + 1
    table.index.name = "position"
    return table


def team_form(team_matches: pd.DataFrame, team: str, season: str, window: int = 5) -> pd.DataFrame:
    """One team's match log for a season, with a rolling points total over `window` matches."""
    log = team_matches.query("team == @team and season == @season").sort_values("date").reset_index(drop=True)
    if log.empty:
        raise ValueError(f"no matches found for team={team!r}, season={season!r}")
    log["matchday"] = range(1, len(log) + 1)
    log["rolling_points"] = log["points"].rolling(window, min_periods=1).sum()
    log["cumulative_points"] = log["points"].cumsum()
    return log[["matchday", "date", "opponent", "venue", "goals_for", "goals_against",
                "outcome", "points", "rolling_points", "cumulative_points"]]


def head_to_head(matches: pd.DataFrame, team_a: str, team_b: str) -> tuple[dict, pd.DataFrame]:
    """All-time record between two teams: a summary dict and the match-by-match log.

    Team order doesn't matter for the summary; the match log keeps each
    fixture's actual home/away venue.
    """
    games = matches[
        ((matches["home_team"] == team_a) & (matches["away_team"] == team_b))
        | ((matches["home_team"] == team_b) & (matches["away_team"] == team_a))
    ].sort_values("date").reset_index(drop=True)
    if games.empty:
        raise ValueError(f"no matches found between {team_a!r} and {team_b!r}")

    a_wins = ((games["home_team"] == team_a) & (games["result"] == "H")).sum() \
        + ((games["away_team"] == team_a) & (games["result"] == "A")).sum()
    b_wins = ((games["home_team"] == team_b) & (games["result"] == "H")).sum() \
        + ((games["away_team"] == team_b) & (games["result"] == "A")).sum()
    draws = (games["result"] == "D").sum()

    summary = {"team_a": team_a, "team_b": team_b, "played": len(games),
               f"{team_a}_wins": int(a_wins), "draws": int(draws), f"{team_b}_wins": int(b_wins)}
    return summary, games
