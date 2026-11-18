"""Paths and tunable constants. Every 'my call' threshold from the design lives here."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
FIG = ROOT / "reports" / "figures"

IPL_COMP_IDS = {1358, 1715, 2193, 2725, 3298}
CURRENT_SEASON = 2026

FULL_MEMBERS = {
    "india", "australia", "england", "newzealand", "southafrica", "pakistan",
    "srilanka", "westindies", "bangladesh", "afghanistan", "ireland", "zimbabwe",
}

# Weights per ball
ASSOCIATE_WEIGHT = 0.5      # T20I / emerging games involving a non-full-member side
RECENCY_DECAY = 0.85        # weight = RECENCY_DECAY ** (2026 - season)

# Pressure definition
PRESSURE_PCT = 0.70         # pressure ball = pressure index in top 30% (within innings 1 / innings 2); tuned on split-half reliability (0.8 and 0.9 were less reliable)
LEVERAGE_SHARE = 0.70       # pressure index = 0.7 * leverage pct + 0.3 * extra-signal pct
CONTEXT_MULT = {            # context filters lower the leverage bar instead of replacing it
    "must_win": 1.35,
    "playoff": 1.50,
    "rivalry": 1.20,
    "bad_form": 1.25,
}

# Filters: id -> (label for batters, label for bowlers, IPL only)
FILTERS = {
    "inn2": ("Chasing pressure", "Defending pressure", False),
    "inn1": ("First-innings pressure", "First-innings pressure", False),
    "must_win": ("Must-win (IPL)", "Must-win (IPL)", True),
    "playoff": ("Playoffs (IPL)", "Playoffs (IPL)", True),
    "rivalry": ("Rivalry (IPL)", "Rivalry (IPL)", True),
    "bad_form": ("Out of form (IPL)", "Out of form (IPL)", True),
}

# Minimum pressure balls per filter (raw count) for a player to be ranked
MIN_BALLS = {
    "bat": {"inn2": 60, "inn1": 60, "must_win": 30, "playoff": 15, "rivalry": 30, "bad_form": 30},
    "bowl": {"inn2": 90, "inn1": 90, "must_win": 42, "playoff": 24, "rivalry": 42, "bad_form": 42},
}

# Score blend inside each filter
COMPONENT_WEIGHTS = {"output": 0.9, "rise": 0.1, "consistency": 0.0}   # tuned on split-half reliability; choke rate stays descriptive (near-zero reliability)

# Inside 'output': weight of runs-above-expected, wicket value and win probability added. Runs above expected is the
# most repeatable part (split-half 0.49 vs 0.21 and 0.17), so it leads; wickets keep real weight, mostly for bowlers.
OUTPUT_WEIGHTS = {"bat": {"sr": 0.8, "wk": 0.1, "wpa": 0.1}, "bowl": {"sr": 0.7, "wk": 0.2, "wpa": 0.1}}
# Shrinkage prior for pressure means: "own" = toward the player's own ordinary-ball level, "league" = league mean
PRIOR = "own"
# Percentiles within role (opener / middle / finisher; powerplay / middle / death) when a group has >= ROLE_MIN_GROUP players
WITHIN_ROLE = True
ROLE_MIN_GROUP = 8
# Cap each player-match mean at these quantiles of its role + filter (robustness: one huge innings cannot carry a player)
WINSOR_PCT = 0.02

# A "pressure innings" (for choke rate) needs at least this many pressure balls in it
MIN_BALLS_PER_INNINGS = 6

# Bad form: last N innings / spells, at least K of them below the player's running baseline
FORM_WINDOW = 5
FORM_BELOW_NEEDED = 4

# Rivalry: number of IPL team pairs flagged
RIVALRY_TOP_PAIRS = 9

# Submission config
SUBMISSION_FILTER_WEIGHTS = {"inn2": 0.35, "inn1": 0.25, "must_win": 0.10, "playoff": 0.15,
                             "rivalry": 0.05, "bad_form": 0.10}
N_BOOT = 1000
SEED = 7
