"""Load the raw files and build one clean ball-level table with the match state before each ball."""
import re

import numpy as np
import pandas as pd

from .config import ASSOCIATE_WEIGHT, CURRENT_SEASON, FULL_MEMBERS, IPL_COMP_IDS, RAW, RECENCY_DECAY

NO_BALLS = {"Overstep", "other"}
ILLEGAL = NO_BALLS | {"wide"}
BOWLER_WICKETS = {"Caught", "Bowled", "LBW", "Stump", "Hit Wicket"}


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", str(name).lower())


def _overs_to_balls(o) -> float:
    if pd.isna(o):
        return np.nan
    o = float(o)
    return int(o) * 6 + round((o - int(o)) * 10)


def load_matches() -> pd.DataFrame:
    m = pd.read_csv(RAW / "matches.csv", parse_dates=["match_date"])
    comps = pd.read_csv(RAW / "competitions.csv")
    m = m.merge(comps[["comp_id", "comp_name", "match_format"]], on="comp_id", how="left")
    m["season"] = m.match_date.dt.year
    m["is_ipl"] = m.comp_id.isin(IPL_COMP_IDS)
    res = m.result.fillna("")
    m["is_tie"] = res.str.contains(r"tied|super over|one over eliminator", case=False)
    m["no_result"] = m.win_team_id.isna()
    m["decided"] = ~m.is_tie & ~m.no_result

    full = m.home_team.map(_norm).isin(FULL_MEMBERS) & m.away_team.map(_norm).isin(FULL_MEMBERS)
    m["tier"] = np.where(m.is_ipl, "IPL", np.where(full & (m.match_format == "T20I"), "T20I", "T20I-assoc"))
    m["tier_weight"] = np.where(m.tier == "T20I-assoc", ASSOCIATE_WEIGHT, 1.0)
    m["recency_weight"] = RECENCY_DECAY ** (CURRENT_SEASON - m.season)
    m["max_balls_1"] = m.first_inn_revised_overs.map(_overs_to_balls).fillna(120)
    m["max_balls_2"] = m.second_inn_revised_overs.map(_overs_to_balls).fillna(m.max_balls_1)
    m = m.sort_values(["match_date", "match_id"]).reset_index(drop=True)
    m["match_seq"] = np.arange(len(m))
    return m


def load_balls(matches: pd.DataFrame) -> pd.DataFrame:
    use = ["match_id", "innings", "innings_ball_num", "batting_team_id", "bowling_team_id", "striker_id",
           "striker_name", "non_striker_id", "bowler_id", "bowler_name", "batting_type", "bowling_type",
           "batting_order", "runs", "is_four", "is_six", "is_wicket", "dismissal_type", "dismissed_player_id",
           "extras_type", "extras1_runs", "extras_2_runs", "pace_or_spin", "overid", "over_ball_num"]
    b = pd.read_csv(RAW / "ball_by_ball.csv", usecols=use)
    b = b[b.innings.isin([1, 2])].copy()                 # drop super overs
    b = b.sort_values(["match_id", "innings", "innings_ball_num"]).reset_index(drop=True)

    ext = b.extras_type.fillna("none")
    b["legal"] = ~ext.isin(ILLEGAL)
    b["faced"] = ext != "wide"                           # a ball the striker faced
    b["total_runs"] = b.runs + b.extras1_runs + b.extras_2_runs
    b["bat_runs"] = b.runs
    bowler_extras = np.where(ext.isin(ILLEGAL), b.extras1_runs + b.extras_2_runs, 0)
    b["bowler_runs"] = b.runs + bowler_extras
    b["is_wicket"] = b.is_wicket.astype(bool)
    b["batter_out"] = b.is_wicket & (b.dismissed_player_id == b.striker_id) & (b.dismissal_type != "Retire Out")
    b["bowler_wicket"] = b.is_wicket & b.dismissal_type.isin(BOWLER_WICKETS)
    b["is_boundary"] = b.is_four.astype(bool) | b.is_six.astype(bool)
    b["is_dot"] = b.legal & (b.total_runs == 0) & ~b.is_wicket

    g = b.groupby(["match_id", "innings"], sort=False)
    b["score_before"] = g.total_runs.cumsum() - b.total_runs
    b["wkts_before"] = g.is_wicket.cumsum() - b.is_wicket
    b["legal_before"] = g.legal.cumsum() - b.legal
    b["inn_total"] = g.total_runs.transform("sum")
    b["inn_wkts"] = g.is_wicket.transform("sum")
    b["inn_legal"] = g.legal.transform("sum")

    mcols = ["match_id", "comp_id", "comp_name", "season", "match_date", "match_seq", "is_ipl", "tier",
             "tier_weight", "recency_weight", "max_balls_1", "max_balls_2", "revised_target", "win_team_id",
             "decided", "knock_out", "stage"]
    b = b.merge(matches[mcols], on="match_id", how="inner")

    b["max_balls"] = np.where(b.innings == 1, b.max_balls_1, b.max_balls_2)
    b["balls_left"] = (b.max_balls - b.legal_before).clip(lower=1)
    b["wih"] = (10 - b.wkts_before).clip(lower=1)        # wickets in hand before the ball
    b["over"] = b.legal_before // 6 + 1
    b["phase"] = pd.cut(b.over, [0, 6, 15, 99], labels=["powerplay", "middle", "death"]).astype(str)

    first_tot = b[b.innings == 1].groupby("match_id").total_runs.sum().rename("first_total")
    b = b.merge(first_tot, on="match_id", how="left")
    b["target"] = b.revised_target.fillna(b.first_total + 1)
    b.loc[b.innings == 1, "target"] = np.nan
    b["runs_needed"] = b.target - b.score_before
    b["rrr"] = (b.runs_needed / b.balls_left * 6).clip(upper=36)
    b["crr"] = np.where(b.legal_before > 0, b.score_before / b.legal_before.clip(lower=1) * 6, 0)
    b["bat_won"] = (b.win_team_id == b.batting_team_id).astype(float)
    b.loc[~b.decided, "bat_won"] = np.nan

    # batter role from batting position in this innings
    b["bat_role"] = pd.cut(b.batting_order, [0, 2, 5, 11], labels=["opener", "middle", "finisher"]).astype(str)
    # balls the striker had faced before this ball (set batter flag)
    b["striker_balls_before"] = b.groupby(["match_id", "innings", "striker_id"]).faced.cumsum() - b.faced
    b["bowler_balls_before"] = b.groupby(["match_id", "innings", "bowler_id"]).legal.cumsum() - b.legal
    b["base_weight"] = b.tier_weight * b.recency_weight
    return b.reset_index(drop=True)


def load_all():
    m = load_matches()
    b = load_balls(m)
    return m, b
