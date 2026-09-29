# AGENTS.md — Premier League Data Study

Guidance for AI agents working in this repo. This is a living document: keep it updated as the user adds context and expectations. Subfolders have their own `AGENTS.md` with more specific rules; the most specific file takes precedence.

## Project
A data study of the English Premier League, using every match result from 1992/93 to the end of 2025/26. It will end up as a Streamlit dashboard.

## Layout
| Path | Purpose |
|---|---|
| `raw_data/epl-<yy>-<yy>/` | Raw source CSVs, one folder per dataset, named by the seasons it covers (see Data). Two football-data.co.uk season files (`2425.csv`, `2526.csv`) sit at the top of `raw_data/` instead. **Read-only: never modify or overwrite.** |
| `notebooks/` | Jupyter notebooks for exploration and analysis (see `notebooks/AGENTS.md`) |
| `scripts/` | Python scripts, e.g. `build_clean_data.py` (see `scripts/AGENTS.md`) |
| `clean_data/` | Merged, cleaned output of `scripts/build_clean_data.py`. **Use this for all analysis and for the dashboard.** It holds **only fields available for every season** (match identity plus full-time score). The schema is in `clean_data/README.md`. Never hand-edit. |
| `app.py` | Streamlit dashboard. Three tabs — League table, Team form, Head-to-head — built on `scripts/data_utils.py` and `clean_data/`. Run: `env -u PYTHONPATH .venv/bin/streamlit run app.py` |
| `.venv/` | Project virtual environment (gitignored) |

## Python environment
- Use the project venv at `.venv/` (Python 3.12, created with `python -m venv .venv`). Never install packages globally.
- **This machine exports `PYTHONPATH=/opt/ros/jazzy/...` (ROS) globally,** which leaks into every venv. `.venv/bin/activate` has been patched to unset it and to restore it on `deactivate`. When calling venv binaries without activating, prefix with `env -u PYTHONPATH`, e.g. `env -u PYTHONPATH .venv/bin/python ...`.
- The patch lives inside the gitignored `.venv/`, so it has to be re-applied if the venv is recreated.
- `requirements.txt` will be the committed dependency record. It doesn't exist yet; the user will say when to create it.
- Installed so far: `pandas`, `jupyter`, `ipykernel`, `nbformat`, `nbconvert`, `matplotlib`, `streamlit`.

## Data
**Analysis should read from `clean_data/`, not `raw_data/`.** Clean data keeps only fields present in every season. Stats available for only some seasons (shots, cards, half-time, xG, matchweek, …) are left out of it on purpose, not added back as partly-empty columns. `raw_data/` is reserved for files the user downloads; the user adds to it and agents never write to it.

Six raw CSVs: four in three dataset folders, plus two season files at the top of `raw_data/`. Each dataset has its own inventory notebook in `notebooks/`.

| Folder | File | Grain | Span | Contents | Notebook |
|---|---|---|---|---|---|
| `epl-92-23/` | `premier-league-matches.csv` | match | 1992/93 – 2022/23 | Full-time score only, plus matchweek (`Wk`) | `03_…` |
| `epl-00-25/` | `epl_final.csv` | match | 2000/01 – 2024/25 | FT/HT scores, shots, shots on target, corners, fouls, cards | `02_…` |
| `epl-25-26/` | `team_match_stats.csv` | team × match | 2025-26 | FBref: xG, possession, formation, referee, etc. | `01_…` |
| `epl-25-26/` | `team_season_stats.csv` | team | 2025-26 | FBref squad standard stats with a 3-row header (`header=[0, 1, 2]`) | `01_…` |
| (top level) | `2425.csv`, `2526.csv` | match | 2024/25, 2025/26 (complete) | football-data.co.uk originals: FT/HT scores, match stats, referee, kick-off time, betting odds | `06_…` |

Known issues:
- **`epl-25-26` is a partial snapshot from about Oct 2025.** `team_match_stats` has results only for MW1–3 (the rest are unplayed fixtures), while `team_season_stats` covers about 8–9 matches per team. The two files are out of sync. Full-season 2025/26 results come from `2526.csv`, which agrees with it on all 30 shared matches.
- **`epl-00-25` is missing 90 matches** (45 each in 2003/04 and 2004/05) and stops at 2025-05-05 (the last 30 matches of 2024/25, which `2425.csv` supplies; the two agree on every shared match, stats included). `epl-92-23` has the missing 2003–05 matches. The two files agree on every overlapping score. The 4 dates that differ (2001-02) were checked against ESPN and Wikipedia, and `epl-00-25` is correct.
- **`epl-00-25` has 3 rows where shots on target are more than total shots** (data-entry errors).
- **Team names differ by source.** `epl-00-25` uses football-data.co.uk short names (`Man United`, `Nott'm Forest`). `epl-92-23` and `epl-25-26` use FBref names (`Manchester Utd`, `Nott'ham Forest`). The crosswalk `TEAM_00_25_TO_92_23` is in notebook 03.
- **Season encodings differ:** `Season_End_Year=2001` (92-23), `Season="2000/01"` (00-25), `season=2526` (25-26). `2425.csv` / `2526.csv` have no season column; derive it from `Date` (`dd/mm/yyyy`). They also start with a byte-order mark, so read them with `encoding="utf-8-sig"`.
- With the two season files, **every season from 1992/93 to 2025/26 is complete** in `clean_data/`.

## Git
- The repo is on branch `main`. No remote is configured yet.
- **The user makes all commits.** Never commit or push, and don't offer to, unless explicitly asked.
