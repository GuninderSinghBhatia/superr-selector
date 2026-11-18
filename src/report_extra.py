"""Extra evidence for the detailed methodology report. Run after `python -m src.report`.

Writes outputs/report_extra.json and more figures in reports/figures:
  threshold sweep, component repeatability, win-probability calibration, pressure map,
  a worked knockout chase, near misses, data coverage."""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from . import build  # noqa: E402
from .config import FIG, OUT, SEED  # noqa: E402
from .reliability import split_half  # noqa: E402
from .report import GREY, INK, PINK, ROYAL, _clean  # noqa: E402


def threshold_sweep(pcts=(0.6, 0.7, 0.8, 0.9)):
    """Rebuild the aggregates at several pressure thresholds and measure split-half repeatability."""
    rows = []
    for pct in pcts:
        _, agg, _, _ = build.run(pct=pct, save=False)
        r = {"pressure_share": round(1 - pct, 2)}
        for role in ("bat", "bowl"):
            d = split_half(agg, role, reps=12)
            r[f"{role}_rho"] = round(float(d.spearman.mean()), 3)
            r[f"{role}_top10"] = round(float(d.top10_overlap.mean()), 1)
            r[f"{role}_ranked"] = int(d.n_common.mean() * 2)  # rough size of the ranked pool across halves
        rows.append(r)
        print(r, flush=True)
    return rows


def component_repeatability(agg, reps=10, min_n=150):
    """Split-half Spearman of each value component, per role, on ordinary and on pressure balls."""
    rng = np.random.default_rng(SEED)
    mids = agg.match_id.unique()
    out = []
    for role in ("bat", "bowl"):
        for label, filt in (("Ordinary balls", ["ordinary"]), ("Pressure balls", ["inn1", "inn2"])):
            a = agg[(agg.role == role) & agg["filter"].isin(filt)]
            res = {c: [] for c in ("sr", "wk", "wpa")}
            n = []
            for _ in range(reps):
                h = set(rng.choice(mids, len(mids) // 2, replace=False))

                def summ(x):
                    g = x.groupby("player_id")[["n", "sw", "s_sr", "s_wk", "s_wpa"]].sum()
                    return g[g.n >= min_n]
                j = summ(a[a.match_id.isin(h)]).join(summ(a[~a.match_id.isin(h)]), how="inner", rsuffix="_b")
                n.append(len(j))
                for c in res:
                    res[c].append(spearmanr(j[f"s_{c}"] / j.sw, j[f"s_{c}_b"] / j.sw_b)[0])
            out.append({"role": role, "balls": label, "players": int(np.mean(n)),
                        **{c: round(float(np.nanmean(v)), 2) for c, v in res.items()}})
    return out


def calibration(b, m):
    d = b.merge(m[["match_id", "win_team_id", "decided"]], on="match_id")
    d = d[d.decided]
    d["won"] = (d.win_team_id == d.batting_team_id).astype(float)
    d["bin"] = pd.cut(d.wp_before, np.linspace(0, 1, 11), include_lowest=True)
    c = d.groupby(["innings", "bin"], observed=True).agg(pred=("wp_before", "mean"), obs=("won", "mean"), n=("won", "size")).reset_index()
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.plot([0, 1], [0, 1], color=GREY, ls=":", lw=1)
    for inn, col in ((1, ROYAL), (2, PINK)):
        x = c[c.innings == inn]
        ax.plot(x.pred, x.obs, "o-", color=col, label=f"Innings {inn}", ms=4)
    ax.set_xlabel("Predicted win probability (batting side)")
    ax.set_ylabel("Share of those balls where the batting side won")
    ax.set_title("Win-probability calibration")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "calibration.png", bbox_inches="tight")
    plt.close(fig)
    gap = float((c.pred - c.obs).abs().mul(c.n).sum() / c.n.sum())
    return round(gap, 3)


def pressure_map(b):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, inn in zip(axes, (1, 2)):
        d = b[(b.innings == inn) & (b.over <= 20)]
        t = d.pivot_table(index="wkts_before", columns="over", values="pi_pct", aggfunc="mean").reindex(index=range(10))
        im = ax.imshow(t.values, aspect="auto", origin="lower", cmap="RdPu", vmin=0.2, vmax=0.9,
                       extent=[0.5, 20.5, -0.5, 9.5])
        ax.set_title(f"Innings {inn}")
        ax.set_xlabel("Over")
        ax.set_xticks([1, 6, 10, 15, 20])
    axes[0].set_ylabel("Wickets down")
    fig.colorbar(im, ax=axes, shrink=0.85, label="Pressure percentile")
    fig.savefig(FIG / "pressure_map.png", bbox_inches="tight")
    plt.close(fig)


def worked_example(b, m):
    """The IPL knock-out chase with the highest average leverage: win probability and pressure ball by ball."""
    ko = m[m.is_ipl & (m.knock_out == 1)][["match_id", "season", "stage", "home_team", "away_team", "result"]]
    d = b[(b.innings == 2) & b.match_id.isin(ko.match_id)]
    mid = d.groupby("match_id").leverage.mean().idxmax()
    x = d[d.match_id == mid].sort_values("innings_ball_num").reset_index(drop=True)
    info = ko.set_index("match_id").loc[mid].to_dict()
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ball = np.arange(1, len(x) + 1)
    ax.fill_between(ball, 0, x.pi_pct, color=PINK, alpha=.18, step="mid", label="Pressure index (percentile)")
    ax.plot(ball, x.wp_before, color=ROYAL, lw=2, label="Chasing side win probability")
    w = x[x.is_wicket]
    ax.scatter(w.index + 1, w.wp_before, color=INK, zorder=3, s=22, label="Wicket")
    ax.axhline(0.7, color=PINK, ls=":", lw=1)
    ax.text(len(x), 0.71, "pressure-ball line", color=PINK, fontsize=7, ha="right", va="bottom")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Ball of the chase")
    ax.set_title(f"Worked example: {info['season']} {info['stage']}, {info['home_team']} v {info['away_team']}")
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3)
    fig.tight_layout()
    fig.savefig(FIG / "worked_example.png", bbox_inches="tight")
    plt.close(fig)
    last = x.iloc[-1]
    return {"season": int(info["season"]), "stage": info["stage"], "teams": f"{info['home_team']} v {info['away_team']}",
            "result": info["result"], "target": int(x.target.iloc[0]), "balls": int(len(x)),
            "pressure_balls": int((x.pi_pct >= 0.7).sum()), "max_leverage": round(float(x.leverage.max()), 3),
            "start_wp": round(float(x.wp_before.iloc[0]), 2), "end_wp": round(float(last.wp_after), 2),
            "series": {"wp": x.wp_before.round(3).tolist(), "pi": x.pi_pct.round(3).tolist(),
                       "wickets": [int(i) for i in np.flatnonzero(x.is_wicket.values)]}}


def near_misses(players):
    boot = pd.read_csv(OUT / "reliability_bootstrap_ranks.csv")
    pl = players.set_index("player_id")
    out = {}
    for role in ("bat", "bowl"):
        x = boot[(boot.role == role) & boot["rank"].between(11, 15)]
        out[role] = [{"rank": int(r["rank"]), "player": pl.name.get(r.player_id, str(r.player_id)),
                      "range": f"{int(r.rank_lo)}–{int(r.rank_hi)}", "p_top10": round(float(r.p_top10), 2)}
                     for _, r in x.iterrows()]
    return out


def coverage(b, m):
    t = m.groupby(["season", "tier"]).size().unstack(fill_value=0)
    balls = b.groupby("tier").size().to_dict()
    return {"matches_by_season_tier": {int(k): v for k, v in t.to_dict("index").items()}, "balls_by_tier": balls,
            "competitions": m.groupby("comp_name").size().sort_values(ascending=False).to_dict()}


def run():
    b = pd.read_parquet(OUT / "balls.parquet")
    m = pd.read_parquet(OUT / "matches.parquet")
    agg = pd.read_parquet(OUT / "agg.parquet")
    players = pd.read_parquet(OUT / "players.parquet")
    extra = {
        "component_repeatability": component_repeatability(agg),
        "calibration_gap": calibration(b, m),
        "worked_example": worked_example(b, m),
        "near_misses": near_misses(players),
        "coverage": coverage(b, m),
    }
    pressure_map(b)
    del b
    extra["threshold_sweep"] = threshold_sweep()
    (OUT / "report_extra.json").write_text(json.dumps(_clean(extra), indent=2, default=str, allow_nan=False))
    print(json.dumps({k: extra[k] for k in ("component_repeatability", "calibration_gap", "worked_example", "near_misses")}, indent=1))
    return extra


if __name__ == "__main__":
    run()
