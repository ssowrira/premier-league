# notebooks/AGENTS.md

Rules for Jupyter notebooks. These extend the root `AGENTS.md`.

## Conventions
- Name notebooks with a two-digit ordered prefix and a snake_case topic. Per-dataset notebooks end with the dataset folder name, e.g. `02_data_inventory_epl_00_25.ipynb`.
- Give each raw dataset folder its own inventory notebook. The two season files at the top of `raw_data/` share one (`06_…`).
- Run with the project `.venv` kernel.
- Resolve paths relative to the repo root so a notebook works whether it's launched from `notebooks/` or the root. The pattern:
  `ROOT = Path.cwd() if (Path.cwd() / "raw_data").exists() else Path.cwd().parent`
- Notebooks 01-03 and 06 read only `raw_data/` (inventory). Later notebooks read `clean_data/` via `load_matches()`.
- **Utility functions live in one place.** Prototype and test a new one in `04_utility_functions.ipynb` first; once it's settled, move it into `scripts/data_utils.py` and replace the notebook definition with an import, so `app.py` and every notebook share one implementation.
- To use `data_utils.py` in a notebook: `sys.path.append(str(ROOT / "scripts")); from data_utils import ...` (see notebook 04's setup cell).
- Chart colors come from the project's validated palette (see the `dataviz` skill, `references/palette.md`): sequential magnitude in blue (`#2a78d6`), diverging pairs in blue/red with gray (`#9a988f`) as the neutral midpoint.
- Commit notebooks after running them, so the outputs can be read on the remote.
- Execute headlessly to check a notebook runs cleanly:
  `cd notebooks && env -u PYTHONPATH ../.venv/bin/jupyter nbconvert --to notebook --execute --inplace <nb>.ipynb`

## Index
| Notebook | Purpose |
|---|---|
| `01_data_inventory_epl_25_26.ipynb` | `raw_data/epl-25-26/`: both FBref CSVs, column dictionaries, played vs scheduled, and the cross-file sync check |
| `02_data_inventory_epl_00_25.ipynb` | `raw_data/epl-00-25/`: column dictionary, season coverage (3 incomplete seasons), and consistency checks |
| `03_data_inventory_epl_92_23.ipynb` | `raw_data/epl-92-23/`: column dictionary, season coverage, consistency checks, and overlap with `epl-00-25` plus the team-name crosswalk |
| `04_utility_functions.ipynb` | Tests and charts the functions in `scripts/data_utils.py` (`load_matches`, `to_team_matches`, `league_table`, `team_form`, `head_to_head`), imported via `sys.path.append`. The reference for how to call each one. |
| `05_man_city_takeover.ipynb` | Manchester City's final position every season (1 Sep 2008 takeover marked); `league_table_excluding_team()` applied to City's 8 post-takeover titles; and, using top-4/5th as a Champions League/Europa League proxy, which clubs would have picked up City's European place across the 18 post-takeover seasons (2008-09 to 2025-26). Written up on the personal website as `ssowrira.github.io/projects/man-city-takeover.html`. |
| `06_data_inventory_football_data_24_26.ipynb` | `raw_data/2425.csv` and `raw_data/2526.csv`: columns (match stats plus betting odds), coverage (both seasons complete), consistency checks, and agreement with `epl-00-25` and `epl-25-26` on every overlapping match |

## Reusable snippets
- Loading `team_season_stats.csv`: `pd.read_csv(..., header=[0, 1, 2])`, then flatten with `flatten()` (per-90 stats get a `_p90` suffix).
- Filter `team_match_stats.csv` to played matches with `result.notna()`.
- Team-name crosswalk from `epl-00-25` to FBref names: `TEAM_00_25_TO_92_23` in notebook 03. Move it to `scripts/` once more than one notebook needs it.
- Convert season encodings to a common key before joining datasets (see root `AGENTS.md`).
- `to_team_matches()` in notebook 04 reshapes `matches.csv` to one row per team per match — use it instead of writing a fresh `(home_team == X) | (away_team == X)` filter each time.
