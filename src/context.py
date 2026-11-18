"""IPL-only match context: rebuilt points tables, must-win flags, rivalry pairs, playoffs."""
import numpy as np
import pandas as pd

from .config import RIVALRY_TOP_PAIRS

LEAGUE_GAMES = 14


def points_tables(m: pd.DataFrame):
    """Replays every IPL league match in date order.

    Returns (per-match-team rows with points before the match, final tables per season)."""
    ipl = m[m.is_ipl & (m.stage == "League")].sort_values(["match_date", "match_id"])
    rows, finals = [], []
    for season, sm in ipl.groupby("season"):
        pts, played = {}, {}
        for r in sm.itertuples():
            teams = (r.home_team_id, r.away_team_id)
            for t, opp in (teams, teams[::-1]):
                rows.append(dict(match_id=r.match_id, season=season, team_id=t, pts_before=pts.get(t, 0),
                                 played_before=played.get(t, 0)))
            for t in teams:
                played[t] = played.get(t, 0) + 1
                if r.no_result:
                    pts[t] = pts.get(t, 0) + 1
                elif r.win_team_id == t:                  # super-over winners get the 2 points
                    pts[t] = pts.get(t, 0) + 2
                else:
                    pts.setdefault(t, 0)
        tbl = pd.Series(pts).sort_values(ascending=False)
        finals.append(dict(season=season, fourth_pts=int(tbl.iloc[3]), fifth_pts=int(tbl.iloc[4]),
                           table=tbl.to_dict(), complete=all(v == LEAGUE_GAMES for v in played.values())))
    return pd.DataFrame(rows), pd.DataFrame(finals)


def must_win_flags(m: pd.DataFrame):
    rows, finals = points_tables(m)
    hist = finals[finals.season <= 2025]
    cutoff = int(hist.fourth_pts.median())               # points a top-4 finish usually needs
    left_after = LEAGUE_GAMES - rows.played_before - 1
    max_if_lose = rows.pts_before + 2 * left_after
    rows["must_win"] = (max_if_lose < cutoff) & (max_if_lose + 2 >= cutoff)
    return rows[["match_id", "team_id", "must_win", "pts_before", "played_before"]], cutoff, finals


def rivalry_pairs(m: pd.DataFrame, b: pd.DataFrame):
    """Rivalry = many meetings, near-even head-to-head, and a history of close finishes (all from the data)."""
    ipl = m[m.is_ipl & m.decided].copy()
    ipl["pair"] = [tuple(sorted(x)) for x in zip(ipl.home_team_id, ipl.away_team_id)]
    # closeness of each game from ball-by-ball: margin <= 12 runs, or chase won with <= 6 balls / <= 3 wickets left
    inn2 = b[b.innings == 2].groupby("match_id").agg(balls_left_end=("balls_left", "last"), legal=("legal", "last"),
                                                     wkts=("inn_wkts", "first"), tot=("inn_total", "first"),
                                                     target=("target", "first"))
    inn2["balls_left_end"] = inn2.balls_left_end - inn2.legal
    ipl = ipl.merge(inn2, left_on="match_id", right_index=True, how="left")
    chase_won = ipl.tot >= ipl.target
    run_margin = ipl.target - 1 - ipl.tot
    ipl["close"] = np.where(chase_won, (ipl.balls_left_end <= 6) | (10 - ipl.wkts <= 3), run_margin <= 12)
    names = pd.concat([m[["home_team_id", "home_team"]].set_axis(["id", "name"], axis=1),
                       m[["away_team_id", "away_team"]].set_axis(["id", "name"], axis=1)]).drop_duplicates("id")
    names = names.set_index("id").name
    ipl["a_won"] = ipl.win_team_id == ipl.pair.map(lambda p: p[0])
    g = ipl.groupby("pair")
    stats = pd.DataFrame({"meetings": g.size(), "wins_a": g.a_won.sum(), "close_share": g.close.mean()})
    stats["h2h_share_a"] = stats.wins_a / stats.meetings
    stats["evenness"] = 1 - 2 * (stats.h2h_share_a - 0.5).abs()
    stats["rivalry_score"] = 0.5 * stats.evenness + 0.5 * stats.close_share
    stats = stats[stats.meetings >= 8].sort_values("rivalry_score", ascending=False)
    stats["team_a"] = [names.get(p[0]) for p in stats.index]
    stats["team_b"] = [names.get(p[1]) for p in stats.index]
    stats["is_rivalry"] = False
    stats.iloc[:RIVALRY_TOP_PAIRS, stats.columns.get_loc("is_rivalry")] = True
    return stats.reset_index()


def match_context(m: pd.DataFrame, b: pd.DataFrame):
    mw, cutoff, finals = must_win_flags(m)
    riv = rivalry_pairs(m, b)
    rpairs = set(riv[riv.is_rivalry].pair)
    ctx = m[["match_id", "home_team_id", "away_team_id", "is_ipl", "knock_out"]].copy()
    ctx["playoff"] = ctx.is_ipl & (ctx.knock_out == 1)
    ctx["rivalry"] = ctx.is_ipl & np.array([tuple(sorted(p)) in rpairs for p in zip(ctx.home_team_id, ctx.away_team_id)])
    return ctx[["match_id", "playoff", "rivalry"]], mw, dict(cutoff=cutoff, finals=finals, rivalry=riv)
