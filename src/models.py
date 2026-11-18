"""Win-probability models (innings 1 and 2), a runs-remaining table, leverage and win probability added."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

# next-ball outcomes used for leverage: (runs, legal ball used, wicket)
OUTCOMES = {"0": (0, 1, 0), "1": (1, 1, 0), "2": (2, 1, 0), "3": (3, 1, 0), "4": (4, 1, 0), "6": (6, 1, 0),
            "W": (0, 1, 1), "X": (1, 0, 0)}


def _outcome_label(b: pd.DataFrame) -> pd.Series:
    r = b.total_runs.clip(upper=6).replace({5: 4})
    lab = r.astype(int).astype(str)
    lab[~b.legal] = "X"
    lab[b.is_wicket] = "W"
    return lab


# ---------------- feature builders (handle terminal states explicitly) ----------------

def _x2(rn, bl, wih, target, ipl):
    rn, bl = np.asarray(rn, float), np.asarray(bl, float)
    rrr = np.clip(rn / np.maximum(bl, 1) * 6, -12, 36)
    return np.column_stack([rn, bl, wih, rrr, target, ipl])


def _x1(score, bl, wih, ipl):
    bl = np.where(np.asarray(wih) <= 0, 0, bl)           # all out == no balls left
    return np.column_stack([score, bl, np.clip(wih, 0, 10), ipl])


class WinProb:
    def __init__(self):
        kw = dict(max_iter=300, learning_rate=0.05, min_samples_leaf=300, l2_regularization=1.0, random_state=0)
        self.m2 = HistGradientBoostingClassifier(monotonic_cst=[-1, 1, 1, -1, 0, 0], **kw)
        self.m1 = HistGradientBoostingClassifier(monotonic_cst=[1, 1, 1, 0], **kw)
        self.metrics = {}

    # --- innings 2 (chasing side's win probability)
    def p2(self, rn, bl, wih, target, ipl):
        rn, bl, wih = np.asarray(rn, float), np.asarray(bl, float), np.asarray(wih, float)
        out = self.m2.predict_proba(_x2(rn, np.maximum(bl, 1), np.maximum(wih, 1), target, ipl))[:, 1]
        out = np.where(rn <= 0, 1.0, out)
        out = np.where((rn > 0) & ((wih <= 0) | (bl <= 0)), np.where(rn == 1, 0.5, 0.0), out)
        return out

    # --- innings 1 (batting-first side's win probability)
    def p1(self, score, bl, wih, ipl):
        return self.m1.predict_proba(_x1(score, bl, wih, ipl))[:, 1]

    def fit(self, b: pd.DataFrame):
        d = b[b.bat_won.notna()]
        ipl = d.is_ipl.astype(float).values
        # innings 2
        d2 = d[d.innings == 2]
        X2 = _x2(d2.runs_needed, d2.balls_left, d2.wih, d2.target, d2.is_ipl.astype(float))
        self.metrics["inn2"] = self._cv(self.m2, X2, d2.bat_won.values, d2.match_id.values)
        self.m2.fit(X2, d2.bat_won.values)
        # innings 1 (+ one terminal row per innings so end-of-innings states are learned)
        d1 = d[d.innings == 1]
        end = d1.groupby("match_id").agg(score=("inn_total", "first"), wih=("inn_wkts", "first"),
                                         ipl=("is_ipl", "first"), y=("bat_won", "first")).reset_index()
        X1 = np.vstack([_x1(d1.score_before, d1.balls_left, d1.wih, d1.is_ipl.astype(float)),
                        _x1(end.score, np.zeros(len(end)), 10 - end.wih, end.ipl.astype(float))])
        y1 = np.concatenate([d1.bat_won.values, end.y.values])
        g1 = np.concatenate([d1.match_id.values, end.match_id.values])
        self.metrics["inn1"] = self._cv(self.m1, X1, y1, g1)
        self.m1.fit(X1, y1)
        return self

    @staticmethod
    def _cv(model, X, y, groups):
        p = np.zeros(len(y))
        for tr, te in GroupKFold(5).split(X, y, groups):
            p[te] = model.fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
        return {"auc": float(roc_auc_score(y, p)), "brier": float(brier_score_loss(y, p)), "n": int(len(y))}


def fit_runs_remaining(b: pd.DataFrame) -> HistGradientBoostingRegressor:
    d = b[(b.innings == 1) & (b.max_balls == 120)]
    X = np.column_stack([d.balls_left, d.wih])
    y = d.inn_total - d.score_before
    return HistGradientBoostingRegressor(monotonic_cst=[1, 1], max_iter=200, min_samples_leaf=200, random_state=0).fit(X, y)


def add_state_values(b: pd.DataFrame, wp: WinProb, re_model) -> pd.DataFrame:
    """Adds wp_before, wp_after, wpa, leverage, wicket cost and the first-innings par deficit."""
    pass  # modified in place to save memory
    lab = _outcome_label(b)
    probs = (pd.crosstab([b.innings, b.phase], lab, normalize="index")
             .reindex(columns=list(OUTCOMES), fill_value=0))
    ipl = b.is_ipl.astype(float).values
    i1, i2 = (b.innings == 1).values, (b.innings == 2).values

    def wp_state(score, rn, bl, wih):
        out = np.empty(len(b))
        out[i1] = wp.p1(score[i1], bl[i1], wih[i1], ipl[i1])
        out[i2] = wp.p2(rn[i2], bl[i2], wih[i2], b.target.values[i2], ipl[i2])
        return out

    score, rn = b.score_before.values.astype(float), b.runs_needed.fillna(0).values
    bl, wih = b.balls_left.values.astype(float), b.wih.values.astype(float)
    b["wp_before"] = wp_state(score, rn, bl, wih)
    b["wp_after"] = wp_state(score + b.total_runs.values, rn - b.total_runs.values,
                             bl - b.legal.values, wih - b.is_wicket.values)
    b["wpa"] = b.wp_after - b.wp_before                 # batting side's gain from this ball

    p = probs.loc[list(zip(b.innings, b.phase))].values
    lev = np.zeros(len(b))
    for k, (r, lg, w) in enumerate(OUTCOMES.values()):
        lev += p[:, k] * np.abs(wp_state(score + r, rn - r, bl - lg, wih - w) - b.wp_before.values)
    b["leverage"] = lev

    # wicket cost in runs (RE24-style) and first-innings par deficit
    re_now = re_model.predict(np.column_stack([bl, wih]))
    re_less = np.where(wih > 1, re_model.predict(np.column_stack([bl, np.maximum(wih - 1, 1)])), 0)
    b["wicket_cost"] = np.clip(re_now - re_less, 0, None)
    proj = score + re_now
    avg_proj = pd.Series(proj).groupby([b.innings.values, b.legal_before.values]).transform("mean").values
    b["par_deficit"] = np.where(i1, avg_proj - proj, np.nan)
    return b
