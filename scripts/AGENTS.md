# scripts/AGENTS.md

Rules for Python scripts. These extend the root `AGENTS.md`.

## Conventions
- Run scripts from the repo root with the venv, e.g. `env -u PYTHONPATH .venv/bin/python scripts/<name>.py`.
- Resolve paths from the script's location (`ROOT = Path(__file__).resolve().parent.parent`), not from the current working directory.
- Scripts read `raw_data/` and never write to it. Processed output goes to `clean_data/`.
- Fail loudly on unexpected data: unmapped team names, duplicate keys, conflicting scores. Don't guess silently.
- Print a short processing log: rows loaded, conflicts resolved, files written.
- **`clean_data/` holds only fields available for every season.** A stat that some sources or seasons lack stays out of clean data. Don't keep it as a partly-empty column. The build asserts there are no missing values.

## Scripts
| Script | Purpose |
|---|---|
| `build_clean_data.py` | Merges all raw datasets (including the football-data.co.uk season files `2425.csv` and `2526.csv`) into `clean_data/` (`matches.csv`, `teams.csv`, `team_aliases.csv`). The output schema and merge rules are in `clean_data/README.md`. |
| `data_utils.py` | Shared functions for loading and analyzing `clean_data/`: `load_matches`, `to_team_matches`, `league_table`, `team_form`, `head_to_head`. Imported by `app.py` and by notebooks. Prototyped and tested in `notebooks/04_utility_functions.ipynb`. |

## `build_clean_data.py`
- **`TEAMS`** is the single source of truth for team names: `(canonical name, short name, 3-letter code, [raw aliases])`. When a new download brings in a new spelling or club, add it here. The script errors until you do.
- **Precedence:** matches come from `epl-92-23`, which is complete to 2022-23. `epl-00-25` supplies 2023-25 and wins on date conflicts. 2025-26 starts from `epl-25-26`. Then `fill_from()` adds whatever is still missing from `2425.csv` and `2526.csv` (the end of 2024-25 and the rest of 2025-26); it fails if one of those files disagrees with an earlier source on any shared match's score or date. Update the merge and `clean_data/README.md` together.
- **New raw data** (e.g. a fresh 2025-26 download) goes into `raw_data/`, gets a loader that returns the common `match_frame()` shape, and joins on `KEY = (season, home_team, away_team)`. Add a new column only if every season can supply it.
- Keep `MATCH_COLUMNS` in step with the column table in `clean_data/README.md`.

## `data_utils.py`
- **Single source of truth** for match/team/table/form/head-to-head logic. `app.py` and notebooks must import from here, not redefine their own version.
- **New functions get prototyped first** in `notebooks/04_utility_functions.ipynb` (defined inline, tested against a known fact, charted), then moved here with the notebook cell replaced by an import. Keep the two in sync.
- Notebooks import it with `sys.path.append(str(ROOT / "scripts"))` before `from data_utils import ...`, since it isn't an installed package.
