"""Merge the raw Premier League datasets into one clean, consistently-formatted data source.

Reads (never modifies) raw_data/ and writes to clean_data/:
    matches.csv       one row per played match, 1992-93 to 2025-26 (the main table)
    teams.csv         canonical team names, short names and 3-letter codes
    team_aliases.csv  every raw team name spelling -> canonical team, by source

Rule: clean data only holds fields that are available for EVERY season. Stats found in only some
sources (half-time scores, shots, cards, xG, possession, matchweek, ...) are left out, not kept as
partly-empty columns. The script checks that no output column has missing values.

Usage (from the repo root):
    env -u PYTHONPATH .venv/bin/python scripts/build_clean_data.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw_data"
OUT = ROOT / "clean_data"

SRC_92_23 = "epl-92-23"
SRC_00_25 = "epl-00-25"
SRC_25_26 = "epl-25-26"
# football-data.co.uk full-season files, saved at the top of raw_data/. They complete 2024-25 and 2025-26.
SRC_FD_24_25 = "2425.csv"
SRC_FD_25_26 = "2526.csv"

# --------------------------------------------------------------------------- teams
# Canonical team (full common name), short name, 3-letter code, and every raw spelling seen in raw_data/.
# Any raw name not listed here makes the script fail, so new downloads can't slip in unmapped names.
TEAMS = [
    ("Arsenal", "Arsenal", "ARS", []),
    ("Aston Villa", "Aston Villa", "AVL", []),
    ("Barnsley", "Barnsley", "BAR", []),
    ("Birmingham City", "Birmingham", "BIR", ["Birmingham"]),
    ("Blackburn Rovers", "Blackburn", "BLB", ["Blackburn"]),
    ("Blackpool", "Blackpool", "BLP", []),
    ("Bolton Wanderers", "Bolton", "BOL", ["Bolton"]),
    ("Bournemouth", "Bournemouth", "BOU", []),
    ("Bradford City", "Bradford", "BRA", ["Bradford"]),
    ("Brentford", "Brentford", "BRE", []),
    ("Brighton & Hove Albion", "Brighton", "BHA", ["Brighton"]),
    ("Burnley", "Burnley", "BUR", []),
    ("Cardiff City", "Cardiff", "CAR", ["Cardiff"]),
    ("Charlton Athletic", "Charlton", "CHA", ["Charlton", "Charlton Ath"]),
    ("Chelsea", "Chelsea", "CHE", []),
    ("Coventry City", "Coventry", "COV", ["Coventry"]),
    ("Crystal Palace", "Crystal Palace", "CRY", []),
    ("Derby County", "Derby", "DER", ["Derby"]),
    ("Everton", "Everton", "EVE", []),
    ("Fulham", "Fulham", "FUL", []),
    ("Huddersfield Town", "Huddersfield", "HUD", ["Huddersfield"]),
    ("Hull City", "Hull", "HUL", ["Hull"]),
    ("Ipswich Town", "Ipswich", "IPS", ["Ipswich"]),
    ("Leeds United", "Leeds", "LEE", ["Leeds"]),
    ("Leicester City", "Leicester", "LEI", ["Leicester"]),
    ("Liverpool", "Liverpool", "LIV", []),
    ("Luton Town", "Luton", "LUT", ["Luton"]),
    ("Manchester City", "Man City", "MCI", ["Man City"]),
    ("Manchester United", "Man Utd", "MUN", ["Man United", "Manchester Utd"]),
    ("Middlesbrough", "Middlesbrough", "MID", []),
    ("Newcastle United", "Newcastle", "NEW", ["Newcastle", "Newcastle Utd"]),
    ("Norwich City", "Norwich", "NOR", ["Norwich"]),
    ("Nottingham Forest", "Nott'm Forest", "NFO", ["Nott'm Forest", "Nott'ham Forest"]),
    ("Oldham Athletic", "Oldham", "OLD", []),
    ("Portsmouth", "Portsmouth", "POR", []),
    ("Queens Park Rangers", "QPR", "QPR", ["QPR"]),
    ("Reading", "Reading", "REA", []),
    ("Sheffield United", "Sheffield Utd", "SHU", ["Sheffield Utd"]),
    ("Sheffield Wednesday", "Sheffield Wed", "SHW", ["Sheffield Weds"]),
    ("Southampton", "Southampton", "SOU", []),
    ("Stoke City", "Stoke", "STK", ["Stoke"]),
    ("Sunderland", "Sunderland", "SUN", []),
    ("Swansea City", "Swansea", "SWA", ["Swansea"]),
    ("Swindon Town", "Swindon", "SWI", []),
    ("Tottenham Hotspur", "Tottenham", "TOT", ["Tottenham"]),
    ("Watford", "Watford", "WAT", []),
    ("West Bromwich Albion", "West Brom", "WBA", ["West Brom"]),
    ("West Ham United", "West Ham", "WHU", ["West Ham"]),
    ("Wigan Athletic", "Wigan", "WIG", ["Wigan"]),
    ("Wimbledon", "Wimbledon", "WIM", []),
    ("Wolverhampton Wanderers", "Wolves", "WOL", ["Wolves"]),
]
TEAM_LOOKUP = {name: team for team, _, _, aliases in TEAMS for name in [team, *aliases]}
TEAM_CODE = {team: code for team, _, code, _ in TEAMS}

# Every column in matches.csv, in output order. Each must be filled for every season.
MATCH_COLUMNS = [
    "match_id", "season", "season_start_year", "date", "day_of_week",
    "home_team", "away_team", "home_team_code", "away_team_code",
    "home_goals", "away_goals", "result", "sources",
]
KEY = ["season", "home_team", "away_team"]  # each pair meets once at each ground per season


def canonical_team(names: pd.Series, source: str) -> pd.Series:
    unknown = sorted(set(names) - TEAM_LOOKUP.keys())
    if unknown:
        raise ValueError(f"{source}: unmapped team names {unknown}. Add them to TEAMS.")
    return names.map(TEAM_LOOKUP)


def season_label(start_year: pd.Series) -> pd.Series:
    """2000 -> '2000-01'"""
    return start_year.astype(str) + "-" + ((start_year + 1) % 100).astype(str).str.zfill(2)


def match_frame(start_year, date, home, away, home_goals, away_goals, source) -> pd.DataFrame:
    """Common shape every loader returns."""
    return pd.DataFrame({
        "season": season_label(start_year),
        "season_start_year": start_year,
        "date": date,
        "home_team": canonical_team(home, source),
        "away_team": canonical_team(away, source),
        "home_goals": home_goals.astype(int),
        "away_goals": away_goals.astype(int),
    }).reset_index(drop=True)


# --------------------------------------------------------------------------- loaders
def load_92_23() -> pd.DataFrame:
    raw = pd.read_csv(RAW / SRC_92_23 / "premier-league-matches.csv", parse_dates=["Date"])
    return match_frame(
        raw["Season_End_Year"] - 1, raw["Date"], raw["Home"], raw["Away"],
        raw["HomeGoals"], raw["AwayGoals"], SRC_92_23,
    )


def load_00_25() -> pd.DataFrame:
    raw = pd.read_csv(RAW / SRC_00_25 / "epl_final.csv", parse_dates=["MatchDate"])
    return match_frame(
        raw["Season"].str[:4].astype(int), raw["MatchDate"], raw["HomeTeam"], raw["AwayTeam"],
        raw["FullTimeHomeGoals"], raw["FullTimeAwayGoals"], SRC_00_25,
    )


def load_25_26() -> pd.DataFrame:
    raw = pd.read_csv(RAW / SRC_25_26 / "team_match_stats.csv", parse_dates=["date"])
    played = raw[raw["result"].notna()]  # drop unplayed fixtures
    home = played[played["venue"] == "Home"]  # one row per match (each match appears once per team)
    assert len(home) * 2 == len(played), f"{SRC_25_26}: played fixtures don't pair up home/away"
    return match_frame(
        2000 + home["season"] // 100,  # season code 2526 -> 2025
        home["date"], home["team"], home["opponent"], home["GF"], home["GA"], SRC_25_26,
    )


def load_football_data(source: str) -> pd.DataFrame:
    """A football-data.co.uk season file (one row per match, dd/mm/yyyy dates)."""
    raw = pd.read_csv(RAW / source, encoding="utf-8-sig")  # files start with a byte-order mark
    assert (raw["Div"] == "E0").all(), f"{source}: expected Premier League (E0) rows only"
    date = pd.to_datetime(raw["Date"], format="%d/%m/%Y")
    start_year = date.dt.year.where(date.dt.month >= 7, date.dt.year - 1)  # Aug-May season
    assert start_year.nunique() == 1, f"{source}: spans more than one season"
    return match_frame(start_year, date, raw["HomeTeam"], raw["AwayTeam"], raw["FTHG"], raw["FTAG"], source)


# --------------------------------------------------------------------------- merge
def fill_from(matches: pd.DataFrame, extra: pd.DataFrame, source: str) -> pd.DataFrame:
    """Add the matches in `extra` that `matches` lacks. Where both have a match, scores and dates
    must agree; the existing row is kept and `source` is appended to its `sources`."""
    both = matches.merge(extra, on=KEY, how="left", suffixes=("", "_new"), indicator=True)["_merge"] == "both"
    overlap = matches[both.values].merge(extra, on=KEY, suffixes=("", "_new"))
    conflict = (
        (overlap["home_goals"] != overlap["home_goals_new"])
        | (overlap["away_goals"] != overlap["away_goals_new"])
        | (overlap["date"].dt.normalize() != overlap["date_new"].dt.normalize())
    )
    assert not conflict.any(), f"{source} disagrees with earlier sources:\n{overlap[conflict]}"

    matches = matches.copy()
    matches.loc[both.values, "sources"] += f";{source}"
    new = extra.merge(matches[KEY], on=KEY, how="left", indicator=True)
    new = new[new["_merge"] == "left_only"].drop(columns="_merge")
    print(f"  {source}: {int(both.sum())} matches confirmed, {len(new)} added")
    return pd.concat([matches, new.assign(sources=source)], ignore_index=True)


def merge_matches(m92: pd.DataFrame, m00: pd.DataFrame, m25: pd.DataFrame,
                  fd24: pd.DataFrame, fd25: pd.DataFrame) -> pd.DataFrame:
    for name, df in [(SRC_92_23, m92), (SRC_00_25, m00), (SRC_25_26, m25), (SRC_FD_24_25, fd24), (SRC_FD_25_26, fd25)]:
        dup = df.duplicated(KEY).sum()
        assert dup == 0, f"{name}: {dup} duplicate (season, home, away) keys"

    both = m92.merge(m00, on=KEY, how="outer", suffixes=("_92", "_00"), indicator=True)
    overlap = both["_merge"] == "both"

    # Scores must agree wherever both sources have the match
    mismatch = overlap & ((both["home_goals_92"] != both["home_goals_00"]) | (both["away_goals_92"] != both["away_goals_00"]))
    assert not mismatch.any(), f"score conflicts between {SRC_92_23} and {SRC_00_25}:\n{both[mismatch][KEY]}"

    # Dates: epl-00-25 wins. The 4 known conflicts (2001-02) were checked against ESPN / Wikipedia
    # and epl-00-25 was right every time.
    date_conflicts = overlap & (both["date_92"] != both["date_00"])
    if date_conflicts.any():
        print(f"  date conflicts resolved in favour of {SRC_00_25}:")
        print("    " + both.loc[date_conflicts, KEY + ["date_92", "date_00"]].to_string(index=False).replace("\n", "\n    "))

    for col in ["season_start_year", "home_goals", "away_goals", "date"]:
        both[col] = both[f"{col}_00"].combine_first(both[f"{col}_92"])
    both["sources"] = both["_merge"].map({"left_only": SRC_92_23, "right_only": SRC_00_25, "both": f"{SRC_92_23};{SRC_00_25}"})
    both = both.drop(columns=[c for c in both.columns if c.endswith(("_92", "_00")) or c == "_merge"])

    overlap_25 = both.merge(m25[KEY], on=KEY)
    assert overlap_25.empty, f"{SRC_25_26} unexpectedly overlaps older sources: {len(overlap_25)} rows"
    matches = pd.concat([both, m25.assign(sources=SRC_25_26)], ignore_index=True)

    # The full-season football-data files fill what the sources above lack (the last 30 matches of
    # 2024-25 and everything after matchweek 3 of 2025-26), and must agree wherever they overlap.
    matches = fill_from(matches, fd24, SRC_FD_24_25)
    matches = fill_from(matches, fd25, SRC_FD_25_26)

    # Derived, uniform fields
    home, away = matches["home_goals"], matches["away_goals"]
    matches["result"] = "D"
    matches.loc[home > away, "result"] = "H"
    matches.loc[home < away, "result"] = "A"
    matches["day_of_week"] = matches["date"].dt.day_name().str[:3]
    matches["home_team_code"] = matches["home_team"].map(TEAM_CODE)
    matches["away_team_code"] = matches["away_team"].map(TEAM_CODE)
    matches["match_id"] = matches["season"] + "_" + matches["home_team_code"] + "_" + matches["away_team_code"]
    for col in ["season_start_year", "home_goals", "away_goals"]:
        matches[col] = matches[col].astype(int)

    matches = matches[MATCH_COLUMNS].sort_values(["date", "home_team"]).reset_index(drop=True)
    matches["date"] = matches["date"].dt.strftime("%Y-%m-%d")

    assert matches["match_id"].is_unique
    gaps = matches.isna().sum()
    assert not gaps.any(), f"clean data must be fully populated; missing values in {gaps[gaps > 0].to_dict()}"
    return matches


def team_tables(matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_names = {
        SRC_92_23: pd.read_csv(RAW / SRC_92_23 / "premier-league-matches.csv", usecols=["Home", "Away"]).stack(),
        SRC_00_25: pd.read_csv(RAW / SRC_00_25 / "epl_final.csv", usecols=["HomeTeam", "AwayTeam"]).stack(),
        SRC_25_26: pd.read_csv(RAW / SRC_25_26 / "team_match_stats.csv", usecols=["team", "opponent"]).stack(),
        **{src: pd.read_csv(RAW / src, encoding="utf-8-sig", usecols=["HomeTeam", "AwayTeam"]).stack()
           for src in [SRC_FD_24_25, SRC_FD_25_26]},
    }
    aliases = pd.DataFrame(
        [(src, name, TEAM_LOOKUP[name]) for src, names in raw_names.items() for name in sorted(set(names))],
        columns=["source", "raw_name", "team"],
    )
    aliases["differs_from_canonical"] = aliases["raw_name"] != aliases["team"]

    long = pd.concat([
        matches[["season", "home_team"]].rename(columns={"home_team": "team"}),
        matches[["season", "away_team"]].rename(columns={"away_team": "team"}),
    ]).drop_duplicates()
    span = long.groupby("team")["season"].agg(first_season="min", last_season="max", seasons_in_data="nunique")
    teams = (
        pd.DataFrame([(t, s, c) for t, s, c, _ in TEAMS], columns=["team", "short_name", "team_code"])
        .join(span, on="team", how="inner")  # only teams that appear in the data
    )
    assert teams["team_code"].is_unique and teams["short_name"].is_unique
    return teams.sort_values("team").reset_index(drop=True), aliases.sort_values(["team", "source"]).reset_index(drop=True)


def report(matches: pd.DataFrame) -> None:
    per_season = matches.groupby("season").agg(matches=("match_id", "size"), teams=("home_team", "nunique"))
    per_season["expected"] = per_season["teams"] * (per_season["teams"] - 1)
    incomplete = per_season[per_season["matches"] != per_season["expected"]]
    print(f"  seasons: {per_season.index.min()} to {per_season.index.max()} ({len(per_season)})")
    if incomplete.empty:
        print("  every season is complete")
    else:
        print("  incomplete seasons (matches / expected):")
        for season, row in incomplete.iterrows():
            print(f"    {season}: {row['matches']} / {row['expected']}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    print("loading raw data")
    m92, m00, m25 = load_92_23(), load_00_25(), load_25_26()
    fd24, fd25 = load_football_data(SRC_FD_24_25), load_football_data(SRC_FD_25_26)
    print(f"  {SRC_92_23}: {len(m92)} matches | {SRC_00_25}: {len(m00)} | {SRC_25_26}: {len(m25)} played"
          f" | {SRC_FD_24_25}: {len(fd24)} | {SRC_FD_25_26}: {len(fd25)}")

    print("merging")
    matches = merge_matches(m92, m00, m25, fd24, fd25)
    teams, aliases = team_tables(matches)
    report(matches)

    outputs = {"matches.csv": matches, "teams.csv": teams, "team_aliases.csv": aliases}
    print(f"writing {OUT.relative_to(ROOT)}/")
    for name, df in outputs.items():
        df.to_csv(OUT / name, index=False)
        print(f"  {name}: {df.shape[0]} rows x {df.shape[1]} cols")

    stale = sorted(p.name for p in OUT.glob("*.csv") if p.name not in outputs)
    if stale:
        print(f"  note: {OUT.relative_to(ROOT)}/ also holds files this script no longer writes: {stale}")


if __name__ == "__main__":
    main()
