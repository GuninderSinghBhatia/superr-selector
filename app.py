"""SupeRR Selector dashboard. Run: streamlit run app.py"""
import html
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from src.config import FILTERS, SUBMISSION_FILTER_WEIGHTS  # noqa: E402
from src.scoring import combine, score_filters  # noqa: E402

OUT = Path(__file__).parent / "outputs"
st.set_page_config(page_title="SupeRR Selector", page_icon=":material/sports_cricket:", layout="wide")

ACCENT, ROYAL, INK, GREY, GOLD = "#ea1a85", "#254aa5", "#0f1e4a", "#a3acc9", "#e9a400"
ICE, FIRE = ROYAL, ACCENT
PALETTE = [ACCENT, ROYAL, GOLD, "#7a5af8", "#0e9f8e", INK]
pio.templates["rr"] = go.layout.Template(layout=dict(
    font=dict(family="DM Sans, system-ui, sans-serif", color=INK), colorway=PALETTE,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="#f3dde9", zerolinecolor="#ead0de"), yaxis=dict(gridcolor="#f3dde9", zerolinecolor="#ead0de"),
    legend=dict(bgcolor="rgba(0,0,0,0)")))
TPL = "plotly_white+rr"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap');
:root {
  --bg:#fff4f9; --surface:#ffffff; --surface-2:#ffe3f0; --tint:#fdeaf3; --tint-blue:#e6ecfa; --line:#f1d6e4;
  --text:#0f1e4a; --muted:#5a6690; --accent:#ea1a85; --accent-text:#c8106f; --royal:#254aa5;
  --good:#0e8a5f; --warn:#a86b00; --bad:#c2410c;
  --shadow:0 1px 2px rgba(37,74,165,.06), 0 10px 28px -6px rgba(37,74,165,.12);
  --ease:cubic-bezier(.16,1,.3,1);
}
.stApp, .stApp button, .stApp input, .stApp textarea {font-family:'DM Sans', system-ui, sans-serif}
.stApp h1, .stApp h2, .stApp h3 {font-family:'Fraunces', Georgia, serif; font-weight:600; color:var(--royal); letter-spacing:-.01em}
::selection {background:var(--accent); color:#fff}
* {scrollbar-width:thin; scrollbar-color:#f0b9d4 transparent}
:focus-visible {outline:2px solid var(--accent); outline-offset:2px; border-radius:6px}
.num {font-variant-numeric:tabular-nums}

@keyframes grow {from{transform:scaleX(0)} to{transform:scaleX(1)}}
@keyframes lift {from{transform:scaleY(0)} to{transform:scaleY(1)}}

/* hero */
.hero {display:flex; gap:16px; align-items:center; margin:0 0 1.3rem}
.hero svg {flex:none; width:46px; height:56px}
.hero h1 {font:600 2.9rem/1 'Fraunces', Georgia, serif; color:var(--royal); margin:0; padding:0; letter-spacing:-.02em; text-wrap:balance}
.hero h1 em {font-style:italic; color:var(--accent-text)}
.hero p {color:var(--muted); margin:.45rem 0 0; max-width:62ch}

/* context pills */
.ctx {display:flex; flex-wrap:wrap; gap:8px; margin:.2rem 0 1rem}
.ctx span {background:var(--surface); border:1px solid var(--line); border-radius:999px; padding:4px 12px; font-size:.85rem; color:var(--muted)}
.ctx span b {color:var(--text); font-weight:600}
.ctx span.on {background:var(--royal); border-color:var(--royal); color:#fff}

/* pin grid: each top-10 player is a card with a Jaipur jharokha arch holding their six filter scores */
.pins {display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:18px; align-items:start; margin:.4rem 0 1.4rem}
.pin {background:var(--surface); border-radius:24px; padding:10px 10px 14px; box-shadow:var(--shadow)}
.arch {position:relative; height:var(--h); border-radius:999px 999px 16px 16px; overflow:hidden;
  background:linear-gradient(180deg, var(--tint-blue) 0%, var(--tint) 100%);
  display:flex; align-items:flex-end; justify-content:center; gap:7px; padding:0 16px 14px}
.pin.lead .arch {background:linear-gradient(180deg, #ffe0ee 0%, #ffc2dd 100%)}
.arch .rk {position:absolute; top:22%; left:0; right:0; text-align:center; font:600 2.4rem/1 'Fraunces', Georgia, serif;
  color:var(--royal); font-variant-numeric:tabular-nums}
.pin.lead .arch .rk {color:var(--accent-text)}
.fp {display:block; width:11px; height:calc(var(--v) * .5%); min-height:4px; border-radius:6px 6px 3px 3px; background:var(--accent);
  transform-origin:bottom; animation:lift 1.1s var(--ease) both}
.fp.ipl {background:var(--royal)}
.fp.na {height:8px; background:transparent; border:1.5px dashed #b4bedb; animation:none}
.pin h3 {font:600 1.02rem/1.25 'DM Sans', sans-serif; color:var(--text); margin:12px 6px 0; padding:0; letter-spacing:0;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; text-wrap:balance}
.pin .sub {color:var(--muted); font-size:.8rem; margin:2px 6px 0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.pin .scr {display:flex; align-items:baseline; gap:6px; margin:10px 6px 6px}
.pin .scr b {font:600 1.9rem/1 'Fraunces', Georgia, serif; color:var(--royal); font-variant-numeric:tabular-nums}
.pin .scr span {color:var(--muted); font-size:.75rem}
.pin .bar {margin:0 6px}
.pin .chips {display:flex; flex-wrap:wrap; gap:6px; margin:10px 4px 0}
.pin .chip::before {content:attr(data-l) " "; color:var(--muted); font-size:.7rem}

/* list view */
.hdr, .row {display:grid; grid-template-columns:36px minmax(0,1.4fr) minmax(0,2fr) 84px 64px 64px;
  grid-template-areas:"rk who bar rng ck n"; gap:12px; align-items:center}
.hdr {padding:0 16px 6px; color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.08em}
.row {padding:12px 16px; border-radius:16px; background:var(--surface); margin-bottom:8px; box-shadow:var(--shadow)}
.row.lead {background:var(--surface-2)}
.row .rk {grid-area:rk; font:600 1.3rem 'Fraunces', Georgia, serif; color:var(--royal); font-variant-numeric:tabular-nums}
.row.lead .rk {color:var(--accent-text)}
.who {grid-area:who; min-width:0}
.who .nm {font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.who .sub {color:var(--muted); font-size:.8rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.barw {grid-area:bar; display:flex; align-items:center; gap:10px}
.bar {flex:1; height:10px; border-radius:5px; background:var(--tint); overflow:hidden}
.bar > i {display:block; height:100%; width:var(--w); border-radius:5px; background:var(--accent);
  transform-origin:left; animation:grow 1.3s var(--ease) both}
.sc {font-weight:600; min-width:2.6ch; text-align:right; font-variant-numeric:tabular-nums}
.chip {font-size:.8rem; padding:3px 9px; border-radius:999px; background:var(--tint); text-align:center;
  color:var(--text); font-variant-numeric:tabular-nums; white-space:nowrap}
.rng {grid-area:rng} .ck {grid-area:ck} .n {grid-area:n}
.chip.ok {color:var(--good)} .chip.warn {color:var(--warn)} .chip.bad {color:var(--bad)}
.hdr .rng, .hdr .ck, .hdr .n {text-align:center}

@media (max-width: 1200px) {.pins {grid-template-columns:repeat(3, minmax(0,1fr))}}
@media (max-width: 720px) {
  .hero h1 {font-size:2.2rem}
  .pins {grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px}
  .hdr {display:none}
  .row {grid-template-columns:30px 1fr 1fr 1fr; grid-template-areas:"rk who who who" ". bar bar bar" ". rng ck n"; row-gap:8px; column-gap:8px}
  .row .chip::before {content:attr(data-l) " "; color:var(--muted); font-size:.72rem}
}
@media (max-width: 440px) {.pins {grid-template-columns:1fr}}
@media (prefers-reduced-motion: reduce) {* {animation:none !important; transition:none !important}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load(_v=0):
    agg = pd.read_parquet(OUT / "agg.parquet")
    pl = pd.read_parquet(OUT / "players.parquet").set_index("player_id")
    return agg, pl


@st.cache_data
def load_balls():
    b = pd.read_parquet(OUT / "balls.parquet", columns=["match_id", "innings", "innings_ball_num", "pi_pct", "wp_before",
                                                        "striker_id", "bowler_id", "is_wicket", "total_runs", "season"])
    m = pd.read_parquet(OUT / "matches.parquet", columns=["match_id", "home_team", "away_team"])
    return b.merge(m, on="match_id", how="left")


@st.cache_data
def load_rel(name):
    f = OUT / f"reliability_{name}.csv"
    return pd.read_csv(f) if f.exists() else None


@st.cache_data
def run_scores(role, filters, seasons, min_scale, _v=0):
    agg, _ = load(_v)
    return score_filters(agg, role, filters=list(filters), seasons=list(seasons), min_scale=min_scale)


_VER = max((OUT / f).stat().st_mtime for f in ("agg.parquet", "players.parquet"))
agg, players = load(_VER)
all_seasons = sorted(agg.season.unique())

# ---------------------------------------------------------------- sidebar
st.sidebar.title("SupeRR Selector")
role_label = st.sidebar.radio("Rank", ["Batters", "Bowlers"], horizontal=True)
role = "bat" if role_label == "Batters" else "bowl"
li = 0 if role == "bat" else 1
st.sidebar.markdown("**Pressure filters**")
weights = {}
for f, spec in FILTERS.items():
    if st.sidebar.checkbox(spec[li], value=True, key=f"c_{f}"):
        weights[f] = st.sidebar.slider(f"{spec[li]} weight", 0.0, 1.0, float(SUBMISSION_FILTER_WEIGHTS[f]), 0.05,
                                       key=f"w_{f}", label_visibility="collapsed")
mode = st.sidebar.radio("Mode", ["All-round", "Specialist"], horizontal=True)
seasons = st.sidebar.select_slider("Seasons", options=all_seasons, value=(all_seasons[0], all_seasons[-1]))
min_scale = st.sidebar.slider("Minimum sample (× default)", 0.5, 2.0, 1.0, 0.1)
if st.sidebar.button("Reset to submission setup"):
    for k in list(st.session_state):
        del st.session_state[k]
    st.rerun()

st.markdown('<div class="hero"><svg viewBox="0 0 46 56" aria-hidden="true">'
            '<path d="M4 54V24a19 19 0 0 1 38 0v30" fill="none" stroke="#ea1a85" stroke-width="3.5" stroke-linecap="round"/>'
            '<path d="M13 54V28a10 10 0 0 1 20 0v26z" fill="#254aa5"/></svg>'
            '<div><h1>SupeRR <em>Selector</em></h1>'
            '<p>Who performs above their own level when the match is on the line — IPL + T20I, ball by ball.</p></div></div>',
            unsafe_allow_html=True)

if not weights or sum(weights.values()) == 0:
    st.info("Tick at least one pressure filter in the sidebar.")
    st.stop()

season_set = tuple(s for s in all_seasons if seasons[0] <= s <= seasons[1])
fs = run_scores(role, tuple(weights), season_set, min_scale, _VER)
res = combine(fs, weights, mode="specialist" if mode == "Specialist" else "allround")
if res.empty:
    st.warning("No player meets the minimum sample for these filters. Lower the minimum sample or add filters.")
    st.stop()
res["Player"] = res.player_id.map(players.name)
res["Team"] = res.player_id.map(players.ipl_team).fillna(res.player_id.map(players.team)).fillna("")
res["Role"] = res.player_id.map(players.bat_role if role == "bat" else players.bowl_phase).fillna("")
top = res.head(10).copy()

# rank ranges are only valid for the submission setup they were bootstrapped on
is_sub = (mode == "All-round" and set(weights) == set(SUBMISSION_FILTER_WEIGHTS) and min_scale == 1.0
          and all(abs(weights[f] - SUBMISSION_FILTER_WEIGHTS[f]) < 1e-9 for f in weights)
          and season_set == tuple(all_seasons))
boot = load_rel("bootstrap_ranks")
if is_sub and boot is not None:
    bb = boot[boot.role == role].set_index("player_id")
    top["lo"] = top.player_id.map(bb.rank_lo)
    top["hi"] = top.player_id.map(bb.rank_hi)
    top["p10"] = top.player_id.map(bb.p_top10)
else:
    top["lo"] = top["hi"] = top["p10"] = np.nan

tab_rank, tab_replay, tab_method = st.tabs(["Rankings", "Pressure replay", "Method and reliability"])

with tab_rank:
    # ---- context line: what is being ranked, and whether rank ranges apply
    setup = "Submission setup, rank ranges shown" if is_sub else "Custom setup, rank ranges hidden"
    st.markdown(f'<div class="ctx"><span><b>Top 10 {role_label.lower()}</b> of {len(res)} ranked</span>'
                f'<span>{len(weights)} of {len(FILTERS)} filters</span><span>{seasons[0]}–{seasons[1]}</span>'
                f'<span>{mode}</span><span class="{"on" if is_sub else ""}">{setup}</span></div>', unsafe_allow_html=True)
    view = st.segmented_control("View", ["Cards", "List"], default="Cards", label_visibility="collapsed") or "Cards"

    # ---- cards: arch height follows the score; the bars inside are the player's six filter scores
    pins = ""
    for i, r in enumerate(top.itertuples()):
        ck = r.choke_rate * 100
        ccls = "ok" if ck < 30 else ("warn" if ck < 45 else "bad")
        rng = f"{int(r.lo)}–{int(r.hi)}" if pd.notna(r.lo) else "n/a"
        h = int(np.clip(118 + (r.score - 55) * 3, 110, 230))
        bars = ""
        for j, f in enumerate(FILTERS):
            v = getattr(r, f"f_{f}", np.nan)
            tip = f"{FILTERS[f][li]}: " + ("not enough balls" if pd.isna(v) else f"{v:.0f}")
            cls = "fp na" if pd.isna(v) else ("fp ipl" if FILTERS[f][2] else "fp")
            bars += (f'<i class="{cls}" title="{html.escape(tip)}" '
                     f'style="--v:{0 if pd.isna(v) else v:.0f};animation-delay:{.1 + i * .05 + j * .04:.2f}s"></i>')
        pins += (f'<article class="pin{" lead" if i == 0 else ""}" aria-label="Rank {r.rank}: {html.escape(str(r.Player))}">'
                 f'<div class="arch" style="--h:{h}px"><span class="rk">{r.rank}</span>{bars}</div>'
                 f'<h3>{html.escape(str(r.Player))}</h3><div class="sub">{html.escape(r.Team)} · {html.escape(r.Role)}</div>'
                 f'<div class="scr"><b>{r.score:.1f}</b><span>pressure score</span></div>'
                 f'<div class="bar"><i style="--w:{r.score:.0f}%;animation-delay:{.2 + i * .05:.2f}s"></i></div>'
                 f'<div class="chips"><span class="chip" data-l="Range" title="Rank range">{rng}</span>'
                 f'<span class="chip {ccls}" data-l="Choke" title="Choke rate">{ck:.0f}%</span>'
                 f'<span class="chip" data-l="Balls" title="Pressure balls">{int(r.pressure_balls)}</span></div></article>')

    # ---- list: the same ten as a scannable table
    rows = ('<div role="table" aria-label="Top 10 by pressure score"><div class="hdr" role="row">'
            '<span role="columnheader">#</span><span role="columnheader">Player</span>'
            '<span role="columnheader">Pressure score</span><span class="rng" role="columnheader">Rank range</span>'
            '<span class="ck" role="columnheader">Choke</span><span class="n" role="columnheader">Balls</span></div>')
    for i, r in enumerate(top.itertuples()):
        ck = r.choke_rate * 100
        ccls = "ok" if ck < 30 else ("warn" if ck < 45 else "bad")
        rng = f"{int(r.lo)}–{int(r.hi)}" if pd.notna(r.lo) else "n/a"
        rows += (f'<div class="row{" lead" if i == 0 else ""}" role="row"><span class="rk" role="cell">{r.rank}</span>'
                 f'<div class="who" role="cell"><div class="nm">{html.escape(str(r.Player))}</div>'
                 f'<div class="sub">{html.escape(r.Team)} · {html.escape(r.Role)}</div></div>'
                 f'<div class="barw" role="cell"><div class="bar"><i style="--w:{r.score:.0f}%;animation-delay:{i * .06}s"></i></div>'
                 f'<span class="sc">{r.score:.1f}</span></div>'
                 f'<span class="chip rng" role="cell" data-l="Range" title="Rank range">{rng}</span>'
                 f'<span class="chip ck {ccls}" role="cell" data-l="Choke" title="Choke rate">{ck:.0f}%</span>'
                 f'<span class="chip n" role="cell" data-l="Balls" title="Pressure balls">{int(r.pressure_balls)}</span></div>')
    if view == "Cards":
        st.markdown(f'<div class="pins">{pins}</div>', unsafe_allow_html=True)
    else:
        st.markdown(rows + "</div>", unsafe_allow_html=True)
    export = top[["rank", "Player", "Team", "Role", "score", "choke_rate", "pressure_balls", "n_filters", "coverage", "lo", "hi"]]
    export = export.rename(columns={"rank": "Rank", "score": "Score", "choke_rate": "Choke rate", "lo": "Rank low", "hi": "Rank high"})
    st.download_button("Export Rank 1–10 as CSV", export.to_csv(index=False), f"top10_{role}.csv", "text/csv",
                       icon=":material/download:")
    with st.expander("How to read the cards and table"):
        st.markdown("**Rank range** is the 5th–95th percentile of a player's rank over 1,000 match resamples. It exists only "
                    "for the submission setup. A high upper bound means the player often drops out of the ranking.  \n"
                    "**Choke** is the share of high-pressure innings below the player's own baseline; lower is better.  \n"
                    "**Balls** is the number of pressure balls behind the score.  \n"
                    "**Arch** (cards view): taller means a higher score. The six bars inside are the player's filter scores, "
                    "left to right: chasing or defending, first innings, must-win, playoffs, rivalry, out of form. Pink bars "
                    "use IPL and T20I matches, blue bars IPL only, and a dashed stub means too few balls to score that filter.")

    # ---- profile + scatter
    labels = {f: FILTERS[f][li] for f in FILTERS}
    pick = st.multiselect("Players to inspect / compare", list(res.Player.head(60)), default=list(top.Player.head(2)))
    left, right = st.columns(2)
    with left:
        st.subheader("Pressure profile")
        cats = [labels[f] for f in FILTERS]
        steps = 8
        traces, finals = [], []
        for i, p in enumerate(pick):
            row = res[res.Player == p].iloc[0]
            vals = [row.get(f"f_{f}") for f in FILTERS]
            vals = [0 if pd.isna(v) else float(v) for v in vals]
            finals.append(vals)
            traces.append(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], name=p, fill="toself",
                                          opacity=.55, line=dict(color=PALETTE[i % 6])))
        frames = [go.Frame(name=str(k), data=[go.Scatterpolar(r=[v * k / steps for v in vals] + [vals[0] * k / steps])
                                              for vals in finals]) for k in range(steps + 1)]
        fig = go.Figure(traces, frames=frames)
        fig.update_layout(
            template=TPL, paper_bgcolor="rgba(0,0,0,0)", height=450, margin=dict(t=30, b=70, l=80, r=80), legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
            polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0, 100], gridcolor="#f3dde9")),
            updatemenus=[dict(type="buttons", direction="left", x=0.0, y=1.08, showactive=False,
                              buttons=[dict(label="Replay", method="animate",
                                            args=[None, dict(frame=dict(duration=70, redraw=True), fromcurrent=False,
                                                             transition=dict(duration=60))])])])
        st.plotly_chart(fig, width="stretch")
        st.caption("Press Replay to redraw the profile. A filter the player does not qualify for (or that is unticked) plots as 0, not as a low score.")
    with right:
        st.subheader("Normal vs pressure")
        pv = fs.groupby("player_id").apply(
            lambda d: pd.Series({"pressure": (d.v * d.n).sum() / d.n.sum(), "ordinary": d.v_ord.mean()}), include_groups=False)
        pv = pv.join(res.set_index("player_id")[["Player"]], how="inner")
        xm, ym = pv.ordinary.median(), pv.pressure.median()
        pv["Type"] = [("Ice" if y >= ym else "Passenger") if x >= xm else ("Fire" if y >= ym else "Choker")
                      for x, y in zip(pv.ordinary, pv.pressure)]
        colors = {"Ice": ICE, "Fire": FIRE, "Choker": GREY, "Passenger": GOLD}
        sc = go.Figure()
        for t, d in pv.groupby("Type"):
            sc.add_trace(go.Scatter(x=d.ordinary, y=d.pressure, mode="markers", name=t, text=d.Player,
                                    hovertemplate="%{text}<extra>" + t + "</extra>",
                                    marker=dict(color=colors[t], size=8, opacity=.75)))
        hi = pv[pv.Player.isin(pick)]
        sc.add_trace(go.Scatter(x=hi.ordinary, y=hi.pressure, mode="markers+text", text=hi.Player, textposition="middle left", cliponaxis=False,
                                name="Selected", marker=dict(size=14, color="white", symbol="diamond", line=dict(width=2.5, color=ACCENT))))
        sc.add_vline(x=xm, line_dash="dot", line_color="#d9b8ca"); sc.add_hline(y=ym, line_dash="dot", line_color="#d9b8ca")
        sc.update_layout(template=TPL, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=430,
                         margin=dict(t=50, b=20), xaxis_title="Ordinary-ball value", yaxis_title="Pressure-ball value", yaxis=dict(automargin=True),
                         transition=dict(duration=500))
        st.plotly_chart(sc, width="stretch")
        st.caption("Ice = good in both · Fire = better under pressure · Choker = worse under pressure · Passenger = good normally, not under pressure.")

    # ---- pressure twins
    if pick:
        wide = res.set_index("Player")[[f"f_{f}" for f in FILTERS if f"f_{f}" in res]].fillna(50)
        v = wide.loc[pick[0]].values
        sim = wide.apply(lambda r: float(np.dot(r.values - 50, v - 50) / ((np.linalg.norm(r.values - 50) * np.linalg.norm(v - 50)) or 1)), axis=1)
        twins = sim.drop(pick[0]).sort_values(ascending=False).head(3)
        st.markdown(f"**Pressure twins of {html.escape(pick[0])}:** " + " · ".join(f"{n} ({s:.2f})" for n, s in twins.items()))

with tab_replay:
    st.subheader("Pressure replay")
    st.caption("Watch the pressure index build through an innings and see which balls the player was involved in.")
    balls = load_balls()
    who = st.selectbox("Player", list(res.Player.head(60)), key="rp_player")
    pid = int(res[res.Player == who].player_id.iloc[0])
    col = "striker_id" if role == "bat" else "bowler_id"
    mine = balls[balls[col] == pid]
    g = (mine.groupby(["match_id", "innings"]).agg(n=("pi_pct", "size"), p=("pi_pct", "mean"), season=("season", "first"),
                                                  home=("home_team", "first"), away=("away_team", "first")).query("n >= 6")
         .sort_values("p", ascending=False).head(12))
    if g.empty:
        st.info("No innings with enough balls for this player.")
    else:
        opts = {f"{int(r.season)} · {r.home} v {r.away} · innings {k[1]} · mean pressure {r.p:.2f}": k for k, r in g.iterrows()}
        sel = opts[st.selectbox("Innings (most pressured first)", list(opts))]
        inn = balls[(balls.match_id == sel[0]) & (balls.innings == sel[1])].sort_values("innings_ball_num").reset_index(drop=True)
        inn["k"] = np.arange(1, len(inn) + 1)
        inn["mine"] = inn[col] == pid
        N = len(inn)
        idx = list(range(4, N + 1, 3)) + ([N] if N % 3 != 1 else [])
        threshold = float(balls.pi_pct.quantile(0.70))

        def part(n):
            d = inn.iloc[:n]
            m_ = d[d.mine]; w_ = m_[m_.is_wicket == 1]
            return [go.Scatter(x=d.k, y=d.pi_pct, mode="lines", line=dict(color=ROYAL, width=2.5)),
                    go.Scatter(x=m_.k, y=m_.pi_pct, mode="markers", marker=dict(color=ACCENT, size=8)),
                    go.Scatter(x=w_.k, y=w_.pi_pct, mode="markers", marker=dict(color=INK, size=15, symbol="x"))]

        base = part(4)
        base[0].name, base[1].name, base[2].name = "Pressure index", f"{who} involved", "Wicket"
        fig = go.Figure(base, frames=[go.Frame(data=part(n), name=str(n)) for n in idx])
        fig.add_hline(y=threshold, line_dash="dot", line_color=GOLD, annotation_text="pressure-ball line")
        fig.update_layout(
            template=TPL, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=440,
            margin=dict(t=20), xaxis=dict(title="Ball of innings", range=[0, N + 2]), yaxis=dict(title="Pressure index (percentile)", range=[0, 1.05]),
            updatemenus=[dict(type="buttons", x=0, y=1.12, showactive=False, direction="left",
                              buttons=[dict(label="Play", method="animate",
                                            args=[None, dict(frame=dict(duration=90, redraw=True), fromcurrent=True, transition=dict(duration=0))]),
                                       dict(label="Pause", method="animate",
                                            args=[[None], dict(frame=dict(duration=0), mode="immediate")])])],
            sliders=[dict(steps=[dict(method="animate", label=str(n), args=[[str(n)], dict(mode="immediate", frame=dict(duration=0, redraw=True))])
                                 for n in idx], x=0.1, len=0.9, currentvalue=dict(prefix="Ball "))])
        st.plotly_chart(fig, width="stretch")

with tab_method:
    st.subheader("How reliable is this ranking?")
    st.markdown("""
Each check re-runs the exact scoring engine on perturbed data. **Read these before trusting any single rank.**
""")
    split, sens, freq, loso = (load_rel(n) for n in ("split_half", "sensitivity", "top10_stability", "leave_one_season_out"))
    if split is None:
        st.info("Reliability tables are still being computed (python -m src.reliability).")
    else:
        sp = split.groupby("role").mean(numeric_only=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Split-half correlation — batters", f"{sp.loc['bat', 'spearman']:.2f}", help="Rank correlation between scores from two random halves of matches. 1 = perfectly repeatable, 0 = noise.")
        c2.metric("Split-half correlation — bowlers", f"{sp.loc['bowl', 'spearman']:.2f}")
        c3.metric("Top-10 overlap between halves — batters", f"{sp.loc['bat', 'top10_overlap']:.1f} / 10")
        c4.metric("Top-10 overlap between halves — bowlers", f"{sp.loc['bowl', 'top10_overlap']:.1f} / 10")
        if sens is not None:
            s = sens.groupby(["weights", "role"]).survivors.mean().unstack()
            st.markdown("**Sensitivity** — average number of the submission top 10 that stay in the top 10 under other setups")
            st.dataframe(s.rename(columns={"bat": "Batters", "bowl": "Bowlers"}).round(1), width="stretch")
        if loso is not None:
            st.markdown("**Leave-one-season-out** — survivors of the top 10 when a season is removed")
            l = loso.pivot(index="dropped_season", columns="role", values="survivors").rename(columns={"bat": "Batters", "bowl": "Bowlers"})
            lf = go.Figure([go.Bar(x=l.index.astype(str), y=l[c], name=c, marker_color=col)
                            for c, col in zip(l.columns, (ACCENT, ICE))])
            lf.update_layout(template=TPL, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280,
                             barmode="group", margin=dict(t=10), yaxis=dict(range=[0, 10], title="Top-10 survivors"),
                             xaxis=dict(title="Season removed"))
            st.plotly_chart(lf, width="stretch")
        if freq is not None:
            f = freq[freq.role == role].copy()
            f["Player"] = f.player_id.map(players.name)
            st.markdown(f"**Top-10 stability** — share of tested setups in which each submitted {role_label.lower()[:-1]} stays top 10")
            fig = go.Figure(go.Bar(x=f.top10_share, y=f.Player, orientation="h", marker_color=ACCENT))
            fig.update_layout(template=TPL, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=360,
                              yaxis=dict(autorange="reversed"), xaxis=dict(range=[0, 1], tickformat=".0%"), margin=dict(t=10))
            st.plotly_chart(fig, width="stretch")
    st.markdown("""
**Method in short**
- Pressure index per ball = 0.7 × leverage percentile (win-probability swing of the next ball) + 0.3 × extra signals; a *pressure ball* is the top 30% within each innings type.
- Value per ball is measured **above expectation** for the phase, bowler type and wickets in hand, adjusted for opposition quality; balls are weighted by recency and down-weighted for associate opposition.
- Values are standardised within competition (IPL vs T20I), and each player-match is capped at the 2nd–98th percentile so one huge innings cannot carry a player.
- Pressure means shrink toward the **player's own ordinary-ball level** (empirical Bayes): with few pressure balls the best guess is "plays as usual", and a gap survives only with evidence.
- Output blends runs above expected, wicket value and win probability added (batters 0.8 / 0.1 / 0.1, bowlers 0.7 / 0.2 / 0.1, set by split-half reliability), plus 10% for the rise over the player's own baseline.
- Scores become 0–100 percentiles **within role** (opener / middle / finisher; powerplay / middle / death bowler), then combine by weight. A player missing a selected filter is filled with a neutral 50, so having fewer filters cannot help.
- Eligibility uses the *effective* (weighted) sample, not raw balls.
- Choke rate is shown but **not scored**: it had near-zero split-half reliability.
""")
