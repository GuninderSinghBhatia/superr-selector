"""Pressure index per ball: leverage plus extra match signals, ranked within innings 1 and innings 2."""
import numpy as np
import pandas as pd

from .config import LEVERAGE_SHARE


def _streak(flag: pd.Series, keys: list[pd.Series]) -> pd.Series:
    """Length of the run of True values ending at the previous ball, within each group."""
    prev = flag.groupby(keys).shift(1, fill_value=False).astype(bool)
    block = (~prev).groupby(keys).cumsum()
    return prev.astype(int).groupby(keys + [block]).cumsum()


def add_signals(b: pd.DataFrame) -> pd.DataFrame:
    pass  # modified in place to save memory
    keys = [b.match_id, b.innings]
    b["dot_streak"] = _streak(b.is_dot | (~b.legal & (b.total_runs == 0)), keys)
    w = b.is_wicket.astype(int)
    b["wkts_last18"] = w.groupby(keys).transform(lambda s: s.shift(1, fill_value=0).rolling(18, min_periods=1).sum())
    b["new_batter_low"] = ((b.striker_balls_before < 6) & (b.wkts_before >= 3) & (b.over <= 15)).astype(int)
    b["set_vs_fresh"] = ((b.striker_balls_before >= 20) & (b.bowler_balls_before < 6)).astype(int)
    b["rate_gap"] = np.where(b.innings == 2, (b.rrr - b.crr).clip(-6, 12), b.par_deficit)
    return b


SIGNALS = ["dot_streak", "wkts_last18", "new_batter_low", "set_vs_fresh", "rate_gap"]


def add_pressure_index(b: pd.DataFrame) -> pd.DataFrame:
    pass  # modified in place to save memory
    g = b.groupby("innings")
    lev_pct = g.leverage.rank(pct=True)
    sig = sum(g[s].rank(pct=True) for s in SIGNALS) / len(SIGNALS)
    b["signal_pct"] = sig.groupby(b.innings).rank(pct=True)
    b["lev_pct"] = lev_pct
    raw = LEVERAGE_SHARE * lev_pct + (1 - LEVERAGE_SHARE) * b.signal_pct
    b["pi_pct"] = raw.groupby(b.innings).rank(pct=True)
    return b


def validation_table(b: pd.DataFrame, pct: float) -> pd.DataFrame:
    """Pressure vs ordinary balls, same innings and phase: does pressure change outcomes?"""
    d = b.assign(pressure=np.where(b.pi_pct >= pct, "pressure", "ordinary"))
    t = d.groupby(["innings", "phase", "pressure"]).agg(
        balls=("legal", "size"), run_rate=("total_runs", "mean"), wicket_pct=("is_wicket", "mean"),
        dot_pct=("is_dot", "mean"), boundary_pct=("is_boundary", "mean"), mean_leverage=("leverage", "mean"))
    t["run_rate"] *= 6
    for c in ["wicket_pct", "dot_pct", "boundary_pct"]:
        t[c] *= 100
    return t.round(3).reset_index()
