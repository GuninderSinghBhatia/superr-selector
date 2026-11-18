"""Reliability checks: bootstrap rank ranges, split-half, sensitivity, leave-one-season-out.

All of them re-run the production engine (`score_filters` + `combine`) on resampled or filtered aggregates."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .config import N_BOOT, OUT, SEED, SUBMISSION_FILTER_WEIGHTS as W
from .scoring import combine, score_filters


def ranked(agg, role, weights=W, **kw):
    fs = score_filters(agg, role, filters=[f for f, w in weights.items() if w > 0], **kw)
    return combine(fs, weights)


def top_ids(res, k=10):
    return list(res.player_id.head(k)) if len(res) else []


def bootstrap_ranks(agg, role, n_boot=N_BOOT, seed=SEED, weights=W):
    """Resample matches with replacement; report each base-top-50 player's 5th-95th percentile rank.
    A player who does not qualify in a resample is given the worst rank for that resample."""
    rng = np.random.default_rng(seed)
    base = ranked(agg, role, weights)
    ids = base.player_id.head(50).tolist()
    mids = agg.match_id.unique()
    ranks = np.full((n_boot, len(ids)), np.nan)
    pos = {p: i for i, p in enumerate(ids)}
    for b in range(n_boot):
        cnt = pd.Series(rng.choice(mids, len(mids)), name="m").value_counts()
        res = ranked(agg, role, weights, boot_w=cnt.to_dict())
        for p, r in zip(res.player_id, res["rank"]):
            if p in pos:
                ranks[b, pos[p]] = r
    worst = len(base) + 1
    ranks = np.where(np.isnan(ranks), worst, ranks)
    out = pd.DataFrame({"player_id": ids, "rank": range(1, len(ids) + 1),
                        "rank_lo": np.percentile(ranks, 5, axis=0).round().astype(int),
                        "rank_hi": np.percentile(ranks, 95, axis=0).round().astype(int),
                        "p_top10": (ranks <= 10).mean(axis=0)})
    out["role"] = role
    return out


def split_half(agg, role, weights=W, reps=20, seed=SEED, **kw):
    """Random half-split of matches (repeated): rank correlation of scores and top-10 overlap between halves."""
    rng = np.random.default_rng(seed)
    mids = agg.match_id.unique()
    rows = []
    for _ in range(reps):
        h = set(rng.choice(mids, len(mids) // 2, replace=False))
        a = ranked(agg[agg.match_id.isin(h)], role, weights, min_scale=0.5, **kw)
        b = ranked(agg[~agg.match_id.isin(h)], role, weights, min_scale=0.5, **kw)
        j = a.merge(b, on="player_id")
        if len(j) > 10:
            rows.append({"n_common": len(j), "spearman": spearmanr(j.score_x, j.score_y)[0],
                         "top10_overlap": len(set(top_ids(a, 10)) & set(top_ids(b, 10))),
                         "top25_overlap": len(set(top_ids(a, 25)) & set(top_ids(b, 25)))})
    return pd.DataFrame(rows).assign(role=role)


def sensitivity(agg, role):
    """Re-rank under different filter weights and minimum samples; count how often each submission top-10 player stays top 10."""
    base = ranked(agg, role)
    base10 = top_ids(base)
    wsets = {
        "submission": W,
        "equal": {f: 1 for f in W},
        "core only (inn1+inn2)": {"inn2": 1, "inn1": 1},
        "chase/defend only": {"inn2": 1},
        "IPL context heavy": {"inn2": .2, "inn1": .1, "must_win": .3, "playoff": .2, "rivalry": .1, "bad_form": .1},
        "no rivalry": {**W, "rivalry": 0},
    }
    rows, hits = [], {p: 0 for p in base10}
    cfgs = [(n, w, s) for n, w in wsets.items() for s in (0.75, 1.0, 1.5)]
    for n, w, s in cfgs:
        res = ranked(agg, role, w, min_scale=s)
        t = top_ids(res)
        for p in t:
            if p in hits:
                hits[p] += 1
        rows.append({"weights": n, "min_scale": s, "survivors": len(set(t) & set(base10))})
    surv = pd.DataFrame(rows).assign(role=role)
    freq = pd.DataFrame({"player_id": base10, "top10_share": [hits[p] / len(cfgs) for p in base10]}).assign(role=role)
    return surv, freq


def leave_one_season_out(agg, role):
    base10 = top_ids(ranked(agg, role))
    rows = []
    for s in sorted(agg.season.unique()):
        t = top_ids(ranked(agg[agg.season != s], role))
        rows.append({"dropped_season": s, "survivors": len(set(t) & set(base10))})
    return pd.DataFrame(rows).assign(role=role)


def run(n_boot=N_BOOT):
    agg = pd.read_parquet(OUT / "agg.parquet")
    parts = {k: [] for k in ("boot", "split", "sens", "freq", "loso")}
    for role in ("bat", "bowl"):
        print(role, "bootstrap...", flush=True)
        parts["boot"].append(bootstrap_ranks(agg, role, n_boot))
        parts["split"].append(split_half(agg, role))
        s, f = sensitivity(agg, role)
        parts["sens"].append(s), parts["freq"].append(f)
        parts["loso"].append(leave_one_season_out(agg, role))
    names = {"boot": "bootstrap_ranks", "split": "split_half", "sens": "sensitivity", "freq": "top10_stability",
             "loso": "leave_one_season_out"}
    for k, v in parts.items():
        pd.concat(v, ignore_index=True).to_csv(OUT / f"reliability_{names[k]}.csv", index=False)
    return parts


if __name__ == "__main__":
    run()
