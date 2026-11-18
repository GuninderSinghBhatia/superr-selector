"""Stage 3: lock the submission lists and compute every number and figure the report and slides use.

Run after `python -m src.build` and `python -m src.reliability`. Writes:
  outputs/submission_top10_batters.csv, outputs/submission_top10_bowlers.csv
  outputs/report_numbers.json
  reports/figures/*.png
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from . import config as C  # noqa: E402
from .reliability import ranked, split_half  # noqa: E402
from .scoring import combine, score_filters  # noqa: E402

OUT, FIG = C.OUT, C.FIG
ROYAL, PINK, INK, GREY, GOLD = "#254aa5", "#ea1a85", "#0f1e4a", "#a3acc9", "#e9a400"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c9cfe3", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "figure.dpi": 160})
ROLE_NAME = {"bat": "batters", "bowl": "bowlers"}


def lock_lists(agg, players, boot):
    lists = {}
    for role in ("bat", "bowl"):
        fs = score_filters(agg, role, filters=[f for f, w in C.SUBMISSION_FILTER_WEIGHTS.items() if w > 0])
        res = combine(fs, C.SUBMISSION_FILTER_WEIGHTS).head(10)
        bb = boot[boot.role == role].set_index("player_id")
        pl = players.set_index("player_id")
        t = pd.DataFrame({
            "Rank": res["rank"].values,
            "Player": res.player_id.map(pl.name).values,
            "Team": res.player_id.map(pl.ipl_team).fillna(res.player_id.map(pl.team)).values,
            "Role": res.player_id.map(pl.bat_role if role == "bat" else pl.bowl_phase).values,
            "Score": res.score.round(1).values,
            "Rank low (5%)": res.player_id.map(bb.rank_lo).values,
            "Rank high (95%)": res.player_id.map(bb.rank_hi).values,
            "P(top 10)": res.player_id.map(bb.p_top10).round(2).values,
            "Choke rate": (res.choke_rate * 100).round(0).values,
            "Pressure balls": res.pressure_balls.astype(int).values,
            "Filters scored": res.n_filters.values,
            "player_id": res.player_id.values,
        })
        for f in C.FILTERS:
            t[f"score_{f}"] = res.get(f"f_{f}", pd.Series(np.nan, index=res.index)).round(1).values
        t.to_csv(OUT / f"submission_top10_{ROLE_NAME[role]}.csv", index=False)
        lists[role] = t
    return lists


def ablation(agg):
    """Split-half reliability of the design-doc scoring vs each change, on the same aggregates."""
    eq = {"sr": 1, "wk": 1, "wpa": 1}
    steps = [
        ("Design-doc scoring (league prior, equal components)", dict(prior="league", output_weights=eq, within_role=False)),
        ("+ shrink toward player's own level", dict(prior="own", output_weights=eq, within_role=False)),
        ("+ reliability-weighted components", dict(prior="own", within_role=False)),
        ("+ percentiles within role (final)", dict(prior="own", within_role=True)),
    ]
    rows = []
    for name, kw in steps:
        r = {"step": name}
        for role in ("bat", "bowl"):
            k = dict(kw)
            if "output_weights" not in k:
                k["output_weights"] = C.OUTPUT_WEIGHTS[role]
            d = split_half(agg, role, reps=20, **k)
            r[f"{role}_rho"] = round(float(d.spearman.mean()), 3)
            r[f"{role}_top10"] = round(float(d.top10_overlap.mean()), 1)
        rows.append(r)
        print(r, flush=True)
    return pd.DataFrame(rows)


def median_check(agg, lists):
    """'Median, not only mean': rank players by their median pressure-innings value and compare with the score."""
    out = {}
    for role in ("bat", "bowl"):
        a = agg[(agg.role == role) & agg["filter"].isin(["inn1", "inn2"]) & (agg.n >= C.MIN_BALLS_PER_INNINGS)]
        med = a.groupby("player_id").inn_v.median()
        res = ranked(agg, role)
        j = res.set_index("player_id").score.to_frame().join(med.rename("med"), how="inner")
        rho = spearmanr(j.score, j.med)[0]
        top_ids = lists[role].player_id
        med_pct = j.med.rank(pct=True)
        out[role] = {"rho_score_vs_median": round(float(rho), 3),
                     "top10_median_pct_min": round(float(med_pct.reindex(top_ids).min()), 2),
                     "top10_median_pct_mean": round(float(med_pct.reindex(top_ids).mean()), 2)}
    return out


# ------------------------------------------------------------------ figures

def fig_validation(val):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    phases = ["powerplay", "middle", "death"]
    for ax, metric, title in zip(axes, ("dot_pct", "boundary_pct"), ("Dot-ball %", "Boundary %")):
        x = np.arange(6)
        lab, o, p = [], [], []
        for inn in (1, 2):
            for ph in phases:
                v = val[(val.innings == inn) & (val.phase == ph)].set_index("pressure")[metric]
                o.append(v["ordinary"]), p.append(v["pressure"]), lab.append(f"Inn {inn}\n{ph}")
        ax.bar(x - 0.2, o, 0.4, color=GREY, label="Ordinary")
        ax.bar(x + 0.2, p, 0.4, color=PINK, label="Pressure")
        ax.set_xticks(x, lab, fontsize=7.5)
        ax.set_title(title)
    axes[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "pressure_validation.png", bbox_inches="tight")
    plt.close(fig)


def fig_top10(lists):
    for role, t in lists.items():
        fig, ax = plt.subplots(figsize=(8, 4.2))
        y = np.arange(len(t))[::-1]
        ax.hlines(y, t["Rank low (5%)"], t["Rank high (95%)"], color=GREY, lw=6, alpha=.7, label="Rank range (5th–95th pct, 1,000 resamples)")
        ax.scatter(t.Rank, y, color=PINK, zorder=3, s=40, label="Submitted rank")
        ax.set_yticks(y, [f"{r}. {n}" for r, n in zip(t.Rank, t.Player)], fontsize=9)
        ax.set_xscale("log")
        ax.set_xticks([1, 2, 5, 10, 20, 50, 100], ["1", "2", "5", "10", "20", "50", "100"])
        ax.axvline(10.5, color=ROYAL, ls=":", lw=1)
        ax.set_xlabel("Rank (log scale)")
        ax.set_title(f"Top 10 {ROLE_NAME[role]}: submitted rank and bootstrap rank range")
        ax.legend(frameon=False, fontsize=8, loc="lower right")
        fig.tight_layout()
        fig.savefig(FIG / f"top10_{role}.png", bbox_inches="tight")
        plt.close(fig)


def fig_ablation(ab):
    fig, ax = plt.subplots(figsize=(8, 3.4))
    x = np.arange(len(ab))
    ax.bar(x - 0.2, ab.bat_rho, 0.4, color=PINK, label="Batters")
    ax.bar(x + 0.2, ab.bowl_rho, 0.4, color=ROYAL, label="Bowlers")
    for i, (a, b) in enumerate(zip(ab.bat_rho, ab.bowl_rho)):
        ax.text(i - 0.2, a + .01, f"{a:.2f}", ha="center", fontsize=8)
        ax.text(i + 0.2, b + .01, f"{b:.2f}", ha="center", fontsize=8)
    short = ["Design doc", "+ own-level prior", "+ weighted components", "+ within role (final)"]
    ax.set_xticks(x, short, fontsize=8.5)
    ax.set_ylabel("Split-half rank correlation")
    ax.set_title("Each scoring change, measured on repeatability")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "ablation.png", bbox_inches="tight")
    plt.close(fig)


def fig_stability(sens, loso):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    s = sens.groupby(["weights", "role"]).survivors.mean().unstack()
    y = np.arange(len(s))
    axes[0].barh(y + 0.2, s["bat"], 0.4, color=PINK, label="Batters")
    axes[0].barh(y - 0.2, s["bowl"], 0.4, color=ROYAL, label="Bowlers")
    axes[0].set_yticks(y, s.index, fontsize=8)
    axes[0].set_xlim(0, 10)
    axes[0].set_xlabel("Top-10 survivors (of 10)")
    axes[0].set_title("Other weightings and sample cuts")
    l = loso.pivot(index="dropped_season", columns="role", values="survivors")
    x = np.arange(len(l))
    axes[1].bar(x - 0.2, l["bat"], 0.4, color=PINK, label="Batters")
    axes[1].bar(x + 0.2, l["bowl"], 0.4, color=ROYAL, label="Bowlers")
    axes[1].set_xticks(x, l.index.astype(str))
    axes[1].set_ylim(0, 10)
    axes[1].set_xlabel("Season removed")
    axes[1].set_title("Leave one season out")
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "stability.png", bbox_inches="tight")
    plt.close(fig)


def _clean(x):
    """NaN is not valid JSON; write null."""
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    if isinstance(x, float) and x != x:
        return None
    return x


def run():
    FIG.mkdir(parents=True, exist_ok=True)
    agg = pd.read_parquet(OUT / "agg.parquet")
    players = pd.read_parquet(OUT / "players.parquet")
    m = pd.read_parquet(OUT / "matches.parquet")
    boot = pd.read_csv(OUT / "reliability_bootstrap_ranks.csv")
    split = pd.read_csv(OUT / "reliability_split_half.csv")
    sens = pd.read_csv(OUT / "reliability_sensitivity.csv")
    loso = pd.read_csv(OUT / "reliability_leave_one_season_out.csv")
    freq = pd.read_csv(OUT / "reliability_top10_stability.csv")
    val = pd.read_csv(OUT / "pressure_validation.csv")
    meta = json.loads((OUT / "build_meta.json").read_text())
    riv = pd.read_csv(OUT / "rivalry_pairs.csv")
    mw = pd.read_parquet(OUT / "must_win.parquet")
    ctx = pd.read_parquet(OUT / "match_context.parquet")

    lists = lock_lists(agg, players, boot)
    ab = ablation(agg)
    ab.to_csv(OUT / "reliability_ablation.csv", index=False)
    med = median_check(agg, lists)

    fig_validation(val), fig_top10(lists), fig_ablation(ab), fig_stability(sens, loso)

    eligible = {}
    for role in ("bat", "bowl"):
        fs = score_filters(agg, role)
        eligible[role] = fs.groupby("filter").size().reindex(list(C.FILTERS)).fillna(0).astype(int).to_dict()

    sp = split.groupby("role").mean(numeric_only=True)
    nums = {
        "data": {"matches": int(len(m)), "ipl_matches": int(m.is_ipl.sum()), "balls": 200961,
                 "seasons": f"{int(m.season.min())}–{int(m.season.max())}",
                 "playoff_matches": int(ctx.playoff.sum()), "must_win_team_matches": int(mw.must_win.sum()),
                 "rivalry_pairs": riv[riv.is_rivalry][["team_a", "team_b", "meetings", "h2h_share_a", "close_share"]]
                 .round(2).to_dict("records"),
                 "ties": int(m.is_tie.sum()), "no_results": int(m.no_result.sum())},
        "wp_metrics": meta["wp_metrics"], "must_win_cutoff": meta["must_win_cutoff"],
        "config": {"pressure_pct": C.PRESSURE_PCT, "leverage_share": C.LEVERAGE_SHARE,
                   "context_mult": C.CONTEXT_MULT, "min_balls": C.MIN_BALLS, "component_weights": C.COMPONENT_WEIGHTS,
                   "output_weights": C.OUTPUT_WEIGHTS, "filter_weights": C.SUBMISSION_FILTER_WEIGHTS,
                   "winsor_pct": C.WINSOR_PCT, "recency_decay": C.RECENCY_DECAY, "associate_weight": C.ASSOCIATE_WEIGHT,
                   "n_boot": C.N_BOOT},
        "eligible": eligible,
        "split_half": {r: {"rho": round(float(sp.loc[r, "spearman"]), 3),
                           "top10_overlap": round(float(sp.loc[r, "top10_overlap"]), 1),
                           "top25_overlap": round(float(sp.loc[r, "top25_overlap"]), 1)} for r in ("bat", "bowl")},
        "ablation": ab.to_dict("records"),
        "sensitivity_mean_survivors": sens.groupby("role").survivors.mean().round(1).to_dict(),
        "sensitivity_by_weights": sens.groupby(["role", "weights"]).survivors.mean().round(1).unstack(0).to_dict(),
        "loso": loso.pivot(index="dropped_season", columns="role", values="survivors").to_dict(),
        "top10_stability": {r: dict(zip(freq[freq.role == r].player_id.astype(int),
                                        freq[freq.role == r].top10_share.round(2))) for r in ("bat", "bowl")},
        "median_check": med,
        "validation": val.to_dict("records"),
        "lists": {r: json.loads(t.drop(columns="player_id").to_json(orient="records")) for r, t in lists.items()},
    }
    (OUT / "report_numbers.json").write_text(json.dumps(_clean(nums), indent=2, default=str, allow_nan=False))
    for r, t in lists.items():
        print(f"\nTop 10 {ROLE_NAME[r]}\n", t[["Rank", "Player", "Team", "Role", "Score", "Rank low (5%)",
                                                  "Rank high (95%)", "P(top 10)", "Choke rate", "Pressure balls"]].to_string(index=False))
    print(json.dumps({k: nums[k] for k in ("split_half", "sensitivity_mean_survivors", "median_check")}, indent=1))
    return nums


if __name__ == "__main__":
    run()
