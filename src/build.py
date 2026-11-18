"""Stage 1: data -> win-probability models -> leverage -> pressure index -> values -> aggregates."""
import json
import time

import pandas as pd

from .config import OUT, PRESSURE_PCT
from .context import match_context
from .data import load_all
from .models import WinProb, add_state_values, fit_runs_remaining
from .pressure import add_pressure_index, add_signals, validation_table
from .scoring import add_values, build_agg, form_flags


def players_table(b: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    team_names = pd.concat([m[["home_team_id", "home_team"]].set_axis(["tid", "team"], axis=1),
                            m[["away_team_id", "away_team"]].set_axis(["tid", "team"], axis=1)]).drop_duplicates("tid")
    tn = team_names.set_index("tid").team
    bat = b[b.faced].sort_values("match_seq").groupby("striker_id").agg(
        name=("striker_name", "last"), bat_role=("bat_role", lambda x: x.mode().iat[0]),
        hand=("batting_type", "last"), last_team=("batting_team_id", "last"),
        balls_faced=("faced", "size"))
    ipl_bat = b[b.faced & b.is_ipl].sort_values("match_seq").groupby("striker_id").batting_team_id.last()
    bowl = b.sort_values("match_seq").groupby("bowler_id").agg(
        name_b=("bowler_name", "last"), bowl_phase=("phase", lambda x: x.mode().iat[0]),
        bowl_type=("bowling_type", "last"), pace_spin=("pace_or_spin", "last"),
        last_team_b=("bowling_team_id", "last"), balls_bowled=("legal", "size"))
    ipl_bowl = b[b.is_ipl].sort_values("match_seq").groupby("bowler_id").bowling_team_id.last()
    p = bat.join(bowl, how="outer")
    p["name"] = p.name.fillna(p.name_b)
    p["team"] = p.last_team.fillna(p.last_team_b).map(tn)
    p["ipl_team"] = ipl_bat.reindex(p.index).fillna(ipl_bowl.reindex(p.index)).map(tn)
    p.index.name = "player_id"
    return p.drop(columns=["name_b", "last_team", "last_team_b"]).reset_index()


def run(pct: float = PRESSURE_PCT, save: bool = True):
    t = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    m, b = load_all()
    wp = WinProb().fit(b)
    re_model = fit_runs_remaining(b)
    b = add_state_values(b, wp, re_model)
    b = add_signals(b)
    b = add_pressure_index(b)
    ctx, mw, info = match_context(m, b)
    b = add_values(b)
    form = form_flags(b)
    agg = build_agg(b, ctx, mw, form, pct)
    print(f"built in {time.time() - t:.0f}s: {len(b)} balls, {len(agg)} agg rows")
    if save:
        keep = ["match_id", "innings", "innings_ball_num", "over", "over_ball_num", "phase", "season", "is_ipl",
                "tier", "batting_team_id", "bowling_team_id", "striker_id", "striker_name", "bowler_id",
                "bowler_name", "total_runs", "bat_runs", "is_wicket", "legal", "faced", "score_before", "wkts_before",
                "balls_left", "target", "runs_needed", "wp_before", "wp_after", "wpa", "leverage", "lev_pct",
                "signal_pct", "pi_pct", "wicket_cost", "par_deficit", "dot_streak", "wkts_last18", "rate_gap",
                "bat_v", "bowl_v", "xR_adj", "xRc_adj", "base_weight"]
        b[keep].to_parquet(OUT / "balls.parquet", index=False)
        agg.to_parquet(OUT / "agg.parquet", index=False)
        players_table(b, m).to_parquet(OUT / "players.parquet", index=False)
        m.to_parquet(OUT / "matches.parquet", index=False)
        ctx.merge(m[["match_id", "season", "home_team", "away_team", "stage"]], on="match_id") \
           .to_parquet(OUT / "match_context.parquet", index=False)
        mw.to_parquet(OUT / "must_win.parquet", index=False)
        form.to_parquet(OUT / "form.parquet", index=False)
        info["rivalry"].assign(pair=info["rivalry"].pair.astype(str)).to_csv(OUT / "rivalry_pairs.csv", index=False)
        validation_table(b, pct).to_csv(OUT / "pressure_validation.csv", index=False)
        fin = info["finals"].drop(columns="table")
        meta = {"wp_metrics": wp.metrics, "must_win_cutoff": info["cutoff"], "finals": fin.to_dict("records"),
                "pressure_pct": pct}
        (OUT / "build_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    return b, agg, m, info


if __name__ == "__main__":
    run()
