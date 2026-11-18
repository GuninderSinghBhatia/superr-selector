"""Per-ball value above expectation, IPL context filters, additive aggregates, and the 0-100 scoring engine.

The engine (`score_filters`, `combine`) works on additive per-(player, filter, match) sums, so the
dashboard, the bootstrap, the season filter and leave-one-season-out all reuse exactly the same code."""
import numpy as np
import pandas as pd

from functools import lru_cache

from .config import (COMPONENT_WEIGHTS, CONTEXT_MULT, FILTERS, FORM_BELOW_NEEDED, FORM_WINDOW, MIN_BALLS,
                     MIN_BALLS_PER_INNINGS, OUT, OUTPUT_WEIGHTS, PRESSURE_PCT, PRIOR, ROLE_MIN_GROUP, WINSOR_PCT,
                     WITHIN_ROLE)

COMPS = ["sr", "wk", "wpa", "v"]
EFFECTIVE_ELIG = True    # eligibility on weight-adjusted sample (down-weights associate-team and old balls)
AVG_W = 0.74             # mean ball weight in the data, so thresholds keep their meaning
SUM_COLS = ["n", "sw", "sw2"] + [f"s_{c}" for c in COMPS] + [f"q_{c}" for c in COMPS] + ["pinn", "choked"]


# --------------------------------------------------------------------------- per-ball values

def _expect(b: pd.DataFrame, mask, col: str, keys: list[str]) -> pd.Series:
    return b[mask].groupby(keys)[col].mean().reindex(pd.MultiIndex.from_frame(b[keys])).values


def _opp_effect(resid: pd.Series, who: pd.Series, k: float) -> pd.Series:
    """Shrunk mean residual of the player on the other side (prior: k balls of league average)."""
    s = resid.groupby(who).agg(["sum", "count"])
    return who.map(s["sum"] / (s["count"] + k)).fillna(0)


def add_values(b: pd.DataFrame) -> pd.DataFrame:
    pass  # modified in place to save memory
    b["tiergrp"] = np.where(b.tier == "IPL", "IPL", "INTL")
    b["wbucket"] = pd.cut(b.wih, [0, 4, 7, 10], labels=["1-4", "5-7", "8-10"]).astype(str)
    keys = ["tiergrp", "innings", "phase", "pace_or_spin", "wbucket", "bat_role"]
    f = b.faced
    b["xR"] = _expect(b, f, "bat_runs", keys)
    b["xW"] = _expect(b, f, "batter_out", keys)
    b["xRc"] = _expect(b, slice(None), "bowler_runs", keys)
    b["xBW"] = _expect(b, slice(None), "bowler_wicket", keys)

    # opposition quality: who was on the other side, relative to league expectation
    bf = b[f]
    bowl_eff_r = _opp_effect(bf.bat_runs - bf.xR, bf.bowler_id, 150)
    bowl_eff_w = _opp_effect(bf.batter_out.astype(float) - bf.xW, bf.bowler_id, 300)
    bat_eff_r = _opp_effect(b.bowler_runs - b.xRc, b.striker_id, 150)
    bat_eff_w = _opp_effect(b.bowler_wicket.astype(float) - b.xBW, b.striker_id, 300)
    b["xR_adj"] = b.xR + bowl_eff_r.reindex(b.index).fillna(0)
    b["xW_adj"] = (b.xW + bowl_eff_w.reindex(b.index).fillna(0)).clip(0.002, 0.6)
    b["xRc_adj"] = b.xRc + bat_eff_r
    b["xBW_adj"] = (b.xBW + bat_eff_w).clip(0.002, 0.6)

    # batting side (only balls faced count for the batter)
    b["bat_sr"] = b.bat_runs - b.xR_adj
    b["bat_wk"] = -b.wicket_cost * (b.batter_out.astype(float) - b.xW_adj)
    b["bat_wpa"] = b.wpa
    b["bat_v"] = b.bat_sr + b.bat_wk
    # bowling side; wickets of set batters (15+ balls faced) earn 25% extra credit
    mult = np.where(b.striker_balls_before >= 15, 1.25, 1.0)
    b["bowl_sr"] = b.xRc_adj - b.bowler_runs
    b["bowl_wk"] = b.wicket_cost * (b.bowler_wicket.astype(float) * mult - b.xBW_adj)
    b["bowl_wpa"] = -b.wpa
    b["bowl_v"] = b.bowl_sr + b.bowl_wk
    return b


# --------------------------------------------------------------------------- bad-form flags

def form_flags(b: pd.DataFrame) -> pd.DataFrame:
    """A player is 'out of form' going into a match when >= 4 of their last 5 innings/spells
    were below their own running baseline (value per ball before that innings)."""
    out = []
    for role, pid, mask, min_n in (("bat", "striker_id", b.faced, 4), ("bowl", "bowler_id", slice(None), 12)):
        d = b[mask].groupby([pid, "match_id"]).agg(n=(f"{role}_v", "size"), s=(f"{role}_v", "sum"),
                                                     seq=("match_seq", "first")).reset_index()
        d = d[d.n >= min_n].sort_values([pid, "seq"])
        g = d.groupby(pid)
        prior_s, prior_n = g.s.cumsum() - d.s, g.n.cumsum() - d.n
        prior_k = g.cumcount()
        base = prior_s / prior_n.replace(0, np.nan)
        below = ((d.s / d.n) < base) & (prior_k >= 10)
        recent = below.astype(int).groupby(d[pid]).transform(lambda s: s.rolling(FORM_WINDOW, min_periods=FORM_WINDOW).sum())
        d["bad_form_next"] = recent >= FORM_BELOW_NEEDED
        d["bad_form"] = d.groupby(pid).bad_form_next.shift(1, fill_value=False).astype(bool)
        out.append(d[[pid, "match_id", "bad_form"]].rename(columns={pid: "player_id"}).assign(role=role))
    return pd.concat(out, ignore_index=True)


# --------------------------------------------------------------------------- aggregation

def build_agg(b: pd.DataFrame, ctx: pd.DataFrame, mw: pd.DataFrame, form: pd.DataFrame,
              pct: float = PRESSURE_PCT) -> pd.DataFrame:
    b = b.merge(ctx, on="match_id", how="left")
    med = b[b.pi_pct >= pct].groupby("innings").leverage.median()
    frames = []
    for role, pid, team, mask in (("bat", "striker_id", "batting_team_id", b.faced.values),
                                  ("bowl", "bowler_id", "bowling_team_id", np.ones(len(b), bool))):
        d = b[mask].copy()
        d["player_id"] = d[pid]
        d = d.merge(mw.rename(columns={"team_id": team}), on=["match_id", team], how="left")
        d = d.merge(form[form.role == role].drop(columns="role"), on=["player_id", "match_id"], how="left")
        d[["must_win", "bad_form"]] = d[["must_win", "bad_form"]].fillna(False).astype(bool)
        d["tiergrp"] = np.where(d.is_ipl, "IPL", "INTL")
        # standardise each value within competition (IPL vs T20I) so a unit means the same in both
        for c in COMPS:
            col = f"{role}_{c}"
            w0 = d.base_weight
            mu = (d[col] * w0).groupby(d.tiergrp).sum() / w0.groupby(d.tiergrp).sum()
            sd = np.sqrt((((d[col] - d.tiergrp.map(mu)) ** 2) * w0).groupby(d.tiergrp).sum() / w0.groupby(d.tiergrp).sum())
            d[col] = d[col] / d.tiergrp.map(sd)
        pi = d.pi_pct.values
        masks = {
            "inn2": (d.innings == 2).values & (pi >= pct),
            "inn1": (d.innings == 1).values & (pi >= pct),
        }
        for f in ("must_win", "playoff", "rivalry", "bad_form"):
            masks[f] = d.is_ipl.values & d[f].fillna(False).values.astype(bool) & (pi * CONTEXT_MULT[f] >= pct)
        masks["ordinary"] = pi < pct
        ln = (d.leverage / d.innings.map(med)).clip(0.5, 3.0).values   # leverage weight on pressure balls
        for f, mk in masks.items():
            x = d[mk]
            w = x.base_weight.values * (1.0 if f == "ordinary" else ln[mk])
            e = pd.DataFrame({"player_id": x.player_id.values, "match_id": x.match_id.values,
                              "season": x.season.values, "tiergrp": x.tiergrp.values, "w": w})
            for c in COMPS:
                v = x[f"{role}_{c}"].values
                e[f"s_{c}"], e[f"q_{c}"] = w * v, w * v * v
            e["w2"] = w * w
            a = e.groupby(["player_id", "match_id", "season", "tiergrp"]).agg(
                n=("w", "size"), sw=("w", "sum"), sw2=("w2", "sum"),
                **{f"s_{c}": (f"s_{c}", "sum") for c in COMPS}, **{f"q_{c}": (f"q_{c}", "sum") for c in COMPS})
            frames.append(a.reset_index().assign(role=role, filter=f))
    agg = pd.concat(frames, ignore_index=True)

    # choke flags per pressure innings: mean value on pressure balls below the player's ordinary baseline
    o = agg[agg["filter"] == "ordinary"].groupby(["role", "player_id"])[["s_v", "sw"]].sum()
    base = (o.s_v / o.sw).rename("base_v")
    agg = agg.merge(base, left_on=["role", "player_id"], right_index=True, how="left")
    is_p = (agg["filter"] != "ordinary") & (agg.n >= MIN_BALLS_PER_INNINGS)
    agg["pinn"] = is_p.astype(float)
    agg["choked"] = (is_p & ((agg.s_v / agg.sw) < agg.base_v.fillna(0))).astype(float)
    agg["inn_v"] = agg.s_v / agg.sw
    return winsorize(agg.drop(columns="base_v"))


# --------------------------------------------------------------------------- scoring engine

def _eb(m, se2, est):
    """Empirical-Bayes shrinkage of player means toward the league mean (method of moments)."""
    if est.sum() < 5:
        return m
    mu = np.nanmean(m[est])
    tau2 = max(np.nanvar(m[est]) - np.nanmean(se2[est]), 0.05 * np.nanvar(m[est]))
    return mu + (m - mu) * tau2 / (tau2 + se2)


def _eb_own(m, se2, prior, est):
    """Shrink a player's pressure mean toward their OWN ordinary-ball level (not the league mean):
    with few pressure balls the best guess is 'plays as usual'; the gap only survives with evidence."""
    d = m - prior
    ok = est & d.notna()
    if ok.sum() < 5:
        return m
    tau2 = max(np.nanvar(d[ok]) - np.nanmean(se2[ok]), 0.05 * np.nanvar(d[ok]))
    return prior + d * tau2 / (tau2 + se2)


@lru_cache(maxsize=1)
def player_roles():
    p = pd.read_parquet(OUT / "players.parquet").set_index("player_id")
    return {"bat": p.bat_role, "bowl": p.bowl_phase}


def winsorize(a: pd.DataFrame, pct: float = WINSOR_PCT) -> pd.DataFrame:
    """Cap each player-match mean at the pct / 1-pct quantiles of its role and filter, so one huge
    innings or spell cannot carry a player (the robust stand-in for a median that stays additive)."""
    if not pct:
        return a
    a = a.copy()
    key = [a.role, a["filter"]]
    for c in COMPS:
        m = a[f"s_{c}"] / a.sw
        lo, hi = m.groupby(key).transform(lambda x: x.quantile(pct)), m.groupby(key).transform(lambda x: x.quantile(1 - pct))
        mc = m.clip(lo, hi)
        ratio = np.where(m != 0, mc / m.replace(0, np.nan), 1.0)
        a[f"s_{c}"] = mc * a.sw
        a[f"q_{c}"] = a[f"q_{c}"] * np.nan_to_num(ratio, nan=1.0) ** 2
    return a


def _pct(x: pd.Series, groups: pd.Series | None) -> pd.Series:
    """Percentile overall, or within role when the role group is big enough."""
    overall = x.rank(pct=True)
    if groups is None:
        return overall
    g = groups.reindex(x.index).fillna("other")
    within = x.groupby(g).rank(pct=True)
    size = g.map(g.value_counts())
    return within.where(size >= ROLE_MIN_GROUP, overall)


def _summ(agg, boot_w=None):
    a = agg
    if boot_w is not None:
        w = a.match_id.map(boot_w).fillna(0).values
        a = a[SUM_COLS].mul(w, axis=0).assign(role=a.role.values, player_id=a.player_id.values,
                                              filter=a["filter"].values)
    return a.groupby(["filter", "player_id"])[SUM_COLS].sum()


def _mean_se(t, c, est):
    m = t[f"s_{c}"] / t.sw
    var = (t[f"q_{c}"] / t.sw - m ** 2).clip(lower=0)
    pooled = (var * t.sw)[est].sum() / t.sw[est].sum()
    neff = t.sw ** 2 / t.sw2
    return m, pooled / neff


def score_filters(agg: pd.DataFrame, role: str, filters=None, seasons=None, min_scale: float = 1.0,
                  comp_weights=None, boot_w=None, output_weights=None, prior=None, within_role=None) -> pd.DataFrame:
    filters = filters or list(FILTERS)
    cw = comp_weights or COMPONENT_WEIGHTS
    ow = output_weights or OUTPUT_WEIGHTS[role]
    prior = prior or PRIOR
    within_role = WITHIN_ROLE if within_role is None else within_role
    groups = player_roles()[role] if within_role else None
    a = agg[(agg.role == role) & agg["filter"].isin(filters + ["ordinary"])]
    if seasons is not None:
        a = a[a.season.isin(seasons)]
    s = _summ(a, boot_w)
    if "ordinary" not in s.index.get_level_values(0):
        return pd.DataFrame()
    o = s.loc["ordinary"]
    o = o[o.sw > 0]
    o_est = o.n >= 60
    ord_eb = {}
    for c in COMPS:
        m_, se_ = _mean_se(o, c, o_est)
        ord_eb[c] = _eb(m_, se_, o_est)
        if c == "v":
            vo_m, vo_se = m_, se_
    vo = ord_eb["v"]
    out = []
    for f in filters:
        if f not in s.index.get_level_values(0):
            continue
        p = s.loc[f]
        p = p[p.sw > 0]
        elig = (p.sw if EFFECTIVE_ELIG else p.n) >= MIN_BALLS[role][f] * min_scale * (AVG_W if EFFECTIVE_ELIG else 1)
        est = p.n >= max(10, MIN_BALLS[role][f] * min_scale / 3)
        r = pd.DataFrame(index=p.index)
        r["n"], r["eligible"] = p.n, elig
        for c in ("sr", "wk", "wpa", "v"):
            m, se2 = _mean_se(p, c, est)
            league = _eb(m, se2, est)
            if prior == "own":
                own = ord_eb[c].reindex(m.index)
                r[c] = _eb_own(m, se2, own.fillna(league), est).where(own.notna(), league)
            else:
                r[c] = league
            if c == "v":
                raw_v, se_v = m, se2
        r["v_ord"] = vo.reindex(r.index)
        d_raw = raw_v - vo_m.reindex(r.index)
        d_se = se_v + vo_se.reindex(r.index)
        r["rise"] = _eb(d_raw, d_se, est & d_raw.notna())
        p0 = p.choked[elig].sum() / max(p.pinn[elig].sum(), 1)
        r["pinn"], r["choke_raw"] = p.pinn, p.choked / p.pinn.replace(0, np.nan)
        r["choke"] = (p.choked + 4 * p0) / (p.pinn + 4)
        r = r[r.eligible].copy()
        if r.empty:
            continue
        pct = lambda x: _pct(x, groups)
        r["output_pct"] = (ow["sr"] * pct(r.sr) + ow["wk"] * pct(r.wk) + ow["wpa"] * pct(r.wpa)) / sum(ow.values())
        r["rise_pct"] = pct(r.rise)
        r["cons_pct"] = pct(-r.choke)
        tot = sum(cw.values())
        r["score"] = 100 * (cw["output"] * r.output_pct + cw["rise"] * r.rise_pct
                            + cw["consistency"] * r.cons_pct) / tot
        r["filter"] = f
        out.append(r.reset_index())
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def combine(fs: pd.DataFrame, filter_weights: dict, mode: str = "allround", missing: str = "neutral",
            min_cover: float = 0.5) -> pd.DataFrame:
    """Overall ranking from per-filter scores.

    mode: 'allround' = weighted average, 'specialist' = best selected filter.
    missing: 'exclude' drops players without every selected filter; 'reweight' averages over the filters they
    qualify for (needs >= min_cover of the selected weight); 'neutral' fills gaps with 50 (same coverage rule)."""
    if fs.empty:
        return pd.DataFrame()
    sel = [f for f, w in filter_weights.items() if w > 0]
    fs = fs[fs["filter"].isin(sel)]
    wide = fs.pivot(index="player_id", columns="filter", values="score").reindex(columns=sel)
    W = pd.Series(filter_weights)[sel]
    have = wide.notna()
    cover = (have * W).sum(axis=1) / W.sum()
    if mode == "specialist":
        overall = wide.max(axis=1)
        keep = have.any(axis=1)
    elif missing == "exclude":
        overall = (wide * W).sum(axis=1) / W.sum()
        keep = have.all(axis=1)
    elif missing == "neutral":
        overall = (wide.fillna(50) * W).sum(axis=1) / W.sum()
        keep = cover >= min_cover
    else:
        overall = (wide.fillna(0) * W).sum(axis=1) / (have * W).sum(axis=1).replace(0, np.nan)
        keep = cover >= min_cover
    balls = fs.groupby("player_id").n.sum().rename("pressure_balls")
    ch = fs.assign(c=fs.choke_raw.fillna(0) * fs.pinn).groupby("player_id")[["c", "pinn"]].sum()
    res = pd.DataFrame({"score": overall, "coverage": cover, "n_filters": have.sum(axis=1)})
    res = res.join(balls).join((ch.c / ch.pinn.replace(0, np.nan)).rename("choke_rate"))
    res = res.join(wide.add_prefix("f_"))
    res = res[keep].sort_values("score", ascending=False)
    res["rank"] = np.arange(1, len(res) + 1)
    return res.reset_index()
