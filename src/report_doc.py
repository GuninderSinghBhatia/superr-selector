"""Writes reports/SupeRR_Selector_R1_Methodology.docx from outputs/report_numbers.json and reports/figures.

Run after `python -m src.report`."""
import json
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from .config import FIG, OUT, ROOT

ROYAL, PINK, INK, MUTED = RGBColor(0x25, 0x4A, 0xA5), RGBColor(0xEA, 0x1A, 0x85), RGBColor(0x0F, 0x1E, 0x4A), RGBColor(0x5A, 0x66, 0x90)
DOCX = ROOT / "reports" / "SupeRR_Selector_R1_Methodology.docx"
FILTER_LABEL = {"inn2": "Chasing / defending", "inn1": "First innings", "must_win": "Must-win (IPL)",
                "playoff": "Playoffs (IPL)", "rivalry": "Rivalry (IPL)", "bad_form": "Out of form (IPL)"}


def shade(cell, hex_):
    tc = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"), sh.set(qn("w:color"), "auto"), sh.set(qn("w:fill"), hex_)
    tc.append(sh)


class Doc:
    def __init__(self):
        self.d = Document()
        st = self.d.styles
        st["Normal"].font.name, st["Normal"].font.size, st["Normal"].font.color.rgb = "Calibri", Pt(11), INK
        for lvl, size in ((1, 18), (2, 14), (3, 12)):
            h = st[f"Heading {lvl}"]
            h.font.name, h.font.size, h.font.color.rgb, h.font.bold = "Cambria", Pt(size), ROYAL, True
        st["Title"].font.name, st["Title"].font.color.rgb, st["Title"].font.size = "Cambria", ROYAL, Pt(28)
        for s in self.d.sections:
            s.left_margin = s.right_margin = Inches(0.9)
            s.top_margin = s.bottom_margin = Inches(0.8)

    def h(self, text, lvl=1):
        self.d.add_heading(text, lvl)

    def p(self, *runs, style=None, after=6):
        para = self.d.add_paragraph(style=style)
        for r in runs:
            if isinstance(r, tuple):
                run = para.add_run(r[0])
                run.bold = "b" in r[1]
                run.italic = "i" in r[1]
            else:
                para.add_run(r)
        para.paragraph_format.space_after = Pt(after)
        return para

    def bullets(self, items):
        for it in items:
            self.p(*(it if isinstance(it, list) else [it]), style="List Bullet", after=2)

    def table(self, header, rows, widths=None, font=9.5):
        t = self.d.add_table(rows=1, cols=len(header))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.style = "Table Grid"
        for i, h in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = ""
            r = c.paragraphs[0].add_run(str(h))
            r.bold, r.font.size, r.font.color.rgb = True, Pt(font), RGBColor(0xFF, 0xFF, 0xFF)
            shade(c, "254AA5")
        for k, row in enumerate(rows):
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                r = cells[i].paragraphs[0].add_run("" if v is None else str(v))
                r.font.size = Pt(font)
                if k % 2 == 0:
                    shade(cells[i], "FDEAF3")
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Inches(w)
        self.d.add_paragraph().paragraph_format.space_after = Pt(2)

    def fig(self, name, caption, width=6.4):
        self.d.add_picture(str(FIG / name), width=Inches(width))
        self.d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = self.p((caption, "i"), after=10)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in cap.runs:
            r.font.size, r.font.color.rgb = Pt(9), MUTED


def fmt_list(rows):
    return [[r["Rank"], r["Player"], r["Team"] or "", r["Role"] or "", f'{r["Score"]:.1f}',
             f'{r["Rank low (5%)"]}–{r["Rank high (95%)"]}', f'{r["P(top 10)"]:.0%}',
             f'{r["Choke rate"]:.0f}%' if r["Choke rate"] is not None else "–", r["Pressure balls"]] for r in rows]


def run():
    N = json.loads((OUT / "report_numbers.json").read_text())
    cfg, D, SH, AB = N["config"], N["data"], N["split_half"], N["ablation"]
    base, fin = AB[0], AB[-1]
    L = N["lists"]
    url = os.environ.get("DASH_URL", "")
    doc = Doc()
    d = doc.d

    d.add_paragraph("SupeRR Selector R1", style="Title")
    doc.p(("Pressure ratings for IPL and T20I players — methodology and results", "b"))
    doc.p(f"Data: {D['matches']} matches ({D['ipl_matches']} IPL), {D['balls']:,} deliveries, {D['seasons']}. "
          "Every number in this report is produced by the same code and tables as the submitted lists and the dashboard.")

    # ------------------------------------------------------------ summary
    doc.h("1. Summary")
    doc.p("We rate each player on how they perform on ", ("pressure balls", "b"),
          " — deliveries where the next ball can swing the match most — measured against what that exact situation "
          "usually yields, adjusted for the opposition, and compared with the player's own usual level. Each submitted "
          "rank carries its own uncertainty: a bootstrap rank range and the probability of staying in the top 10.")
    doc.bullets([
        [("Pressure is defined per ball", "b"), f" from win-probability leverage plus five match signals; the top "
         f"{round((1 - cfg['pressure_pct']) * 100)}% of balls in each innings type are pressure balls. Four IPL-only "
         "context filters (must-win, playoffs, rivalry, out of form) add weight on top."],
        [("Scores are above expectation", "b"), ", standardised within IPL and within T20I, shrunk toward the "
         "player's own level, and turned into 0–100 percentiles within role."],
        [("The ranking repeats itself", "b"), f": split-half rank correlation {SH['bat']['rho']:.2f} for batters and "
         f"{SH['bowl']['rho']:.2f} for bowlers (from {base['bat_rho']:.2f} and {base['bowl_rho']:.2f} in our first draft); "
         f"on average {N['sensitivity_mean_survivors']['bat']} batters and {N['sensitivity_mean_survivors']['bowl']} bowlers "
         "of the top 10 stay in the top 10 across the alternative weightings and sample cuts we tested."],
    ])

    # ------------------------------------------------------------ lists
    doc.h("2. Submitted lists")
    hdr = ["#", "Player", "Team", "Role", "Score", "Rank range", "P(top 10)", "Choke", "Pressure balls"]
    w = [0.3, 1.5, 1.45, 0.75, 0.5, 0.75, 0.65, 0.5, 0.65]
    doc.h("Top 10 batters", 3)
    doc.table(hdr, fmt_list(L["bat"]), w)
    doc.h("Top 10 bowlers", 3)
    doc.table(hdr, fmt_list(L["bowl"]), w)
    doc.p(("How to read these columns. ", "b"),
          "Score is the weighted 0–100 pressure score. Rank range is the 5th–95th percentile of the player's rank "
          f"over {cfg['n_boot']:,} resamples of matches. P(top 10) is the share of resamples in which the player stays top 10. "
          "Choke is the share of the player's pressure innings or spells below their own ordinary level (shown, not scored; "
          "see section 6). Pressure balls is the sample behind the score. Team is the player's latest IPL side where they have one.")
    doc.fig("top10_bat.png", "Figure 1. Submitted batters with their bootstrap rank ranges.")
    doc.fig("top10_bowl.png", "Figure 2. Submitted bowlers with their bootstrap rank ranges.")

    # ------------------------------------------------------------ data
    doc.h("3. Data and preparation")
    doc.bullets([
        f"Ball-by-ball, matches, playing elevens, competitions, teams and player mapping, as supplied. Super overs are excluded.",
        f"Ties ({D['ties']}) and no-results ({D['no_results']}) are excluded from win-probability training; no-results add no result-based credit.",
        "Rain-affected matches use the revised target and overs where the data has them.",
        "IPL points tables are not in the data, so we replay every IPL league match in date order to rebuild them "
        f"(super-over winners get the points). A top-4 finish needed a median of {N['must_win_cutoff']} points in 2022–2025.",
        f"Balls are weighted by recency (×{cfg['recency_decay']} per season back) and associate-team T20Is by ×{cfg['associate_weight']}.",
    ])

    # ------------------------------------------------------------ pressure
    doc.h("4. What counts as pressure")
    doc.h("4.1 Leverage from win probability", 2)
    wp = N["wp_metrics"]
    doc.p("Two gradient-boosted win-probability models (monotonic in runs, balls and wickets) give the batting side's "
          "chance of winning before every ball. Chasing uses runs needed, balls left, wickets in hand, required rate and "
          f"target (cross-validated AUC {wp['inn2']['auc']:.2f}, Brier {wp['inn2']['brier']:.3f}). The first innings, which has "
          f"no target, uses score, balls left and wickets in hand against what teams go on to reach (AUC {wp['inn1']['auc']:.2f}). "
          "Leverage is the expected absolute change in win probability over the next ball's possible outcomes, using "
          "outcome frequencies for that innings and phase. Read from the bowling side, the same number measures defending pressure.")
    doc.h("4.2 Pressure index and pressure balls", 2)
    doc.p(f"Pressure index = {round(cfg['leverage_share'] * 100)}% leverage percentile + "
          f"{round((1 - cfg['leverage_share']) * 100)}% average percentile of five signals: dot-ball streak, wickets in the "
          "last three overs, a new batter arriving at a low score, the gap between current and required rate (or the "
          "first-innings par deficit), and a set batter facing a fresh bowler. A pressure ball is in the top "
          f"{round((1 - cfg['pressure_pct']) * 100)}% of the index within its innings type.")
    doc.h("4.3 IPL context filters", 2)
    riv = ", ".join(f"{r['team_a']} v {r['team_b']}" for r in D["rivalry_pairs"])
    doc.bullets([
        [("Must-win: ", "b"), f"a loss would leave the team unable to reach {N['must_win_cutoff']} points while a win keeps it alive "
         f"({D['must_win_team_matches']} team-matches)."],
        [("Playoffs: ", "b"), f"knock-out matches ({D['playoff_matches']} IPL matches)."],
        [("Rivalry: ", "b"), f"pairs with 8+ meetings, ranked by an even head-to-head and a high share of close finishes; the top "
         f"{len(D['rivalry_pairs'])} are flagged: {riv}."],
        [("Out of form: ", "b"), "at least 4 of the player's last 5 innings or spells were below their own running baseline; the filter covers the next match."],
    ])
    mult = ", ".join(f"{FILTER_LABEL[k].split(' (')[0].lower()} ×{v}" for k, v in cfg["context_mult"].items())
    doc.p("Context filters lower the bar instead of replacing it: a ball in a context match counts when its pressure index "
          f"times the context multiplier ({mult}) clears the same threshold. A quiet over in a final is not counted on its own.")
    doc.h("4.4 Does the definition separate pressure from ordinary play?", 2)
    V = {(r["innings"], r["phase"], r["pressure"]): r for r in N["validation"]}
    more_dots = sum(V[(i, p, "pressure")]["dot_pct"] > V[(i, p, "ordinary")]["dot_pct"] for i in (1, 2) for p in ("powerplay", "middle", "death"))
    lower_rr = sum(V[(i, p, "pressure")]["run_rate"] < V[(i, p, "ordinary")]["run_rate"] for i in (1, 2) for p in ("powerplay", "middle", "death"))
    d2p, d2o = V[(2, "death", "pressure")], V[(2, "death", "ordinary")]
    doc.p(f"Compared within the same innings and phase, pressure balls go for fewer runs in {lower_rr} of 6 phases and "
          f"bring more dot balls in {more_dots} of 6. The exception is the end of a chase: batters needing a big finish have to swing, so "
          f"pressure balls in the death overs of innings 2 go at {d2p['run_rate']:.1f} an over against {d2o['run_rate']:.1f}, with more "
          f"wickets ({d2p['wicket_pct']:.1f}% vs {d2o['wicket_pct']:.1f}%). In the first innings, pressure shows up as caution "
          "(more dots, fewer boundaries) rather than more wickets. This is why the score measures performance against the "
          "expectation for each situation rather than raw runs or wickets.")
    doc.fig("pressure_validation.png", "Figure 3. Dot-ball and boundary rates on ordinary and pressure balls, by innings and phase.")
    doc.table(["Innings", "Phase", "Ball type", "Balls", "Run rate", "Wicket %", "Dot %", "Boundary %"],
              [[r["innings"], r["phase"], r["pressure"], f"{r['balls']:,}", f"{r['run_rate']:.2f}", f"{r['wicket_pct']:.2f}",
                f"{r['dot_pct']:.1f}", f"{r['boundary_pct']:.1f}"] for r in N["validation"]], font=9)

    # ------------------------------------------------------------ scoring
    doc.h("5. Scoring")
    doc.h("5.1 Value above expectation", 2)
    doc.p("For every ball we compute what the league usually gets from the same situation: competition (IPL or T20I), "
          "innings, phase, pace or spin, wickets in hand and batting position. We then adjust for the player on the other side "
          "using their shrunk average effect. Three components follow:")
    doc.bullets([
        [("Runs vs expected", "b"), ": runs scored above expectation (batters) or conceded below it (bowlers)."],
        [("Wicket value", "b"), ": dismissals against expectation, priced in runs by what a wicket costs from that state; bowlers get 25% extra for wickets of set batters (15+ balls)."],
        [("Win probability added", "b"), ": the change in the batting side's win probability on that ball (negated for bowlers)."],
    ])
    doc.p("Each component is standardised within IPL and within T20I, so a unit means the same in both. Pressure balls are "
          "weighted by their leverage relative to a typical pressure ball (capped 0.5–3×). Each player-match average is "
          f"capped at the {cfg['winsor_pct']:.0%}–{1 - cfg['winsor_pct']:.0%} quantiles of its role and filter, so one huge innings cannot carry a player.")
    doc.h("5.2 From value to a 0–100 score", 2)
    ow = cfg["output_weights"]
    doc.bullets([
        [("Shrinkage toward the player's own level. ", "b"), "Pressure samples are small. The best guess for a player with few "
         "pressure balls is that they play as usual, so each pressure average is shrunk (empirical Bayes) toward the same "
         "player's ordinary-ball level, by an amount set by its sampling error. A gap from normal survives only with evidence."],
        [("Output. ", "b"), f"Percentiles of the three components, weighted {ow['bat']['sr']}/{ow['bat']['wk']}/{ow['bat']['wpa']} for batters and "
         f"{ow['bowl']['sr']}/{ow['bowl']['wk']}/{ow['bowl']['wpa']} for bowlers (runs / wickets / win probability). Runs vs expected leads because it is "
         "the most repeatable part (section 6)."],
        [("Rise. ", "b"), f"The shrunk gap between pressure and ordinary value. Score = {cfg['component_weights']['output']:.0%} output + "
         f"{cfg['component_weights']['rise']:.0%} rise."],
        [("Within role. ", "b"), "Percentiles are taken within openers, middle order and finishers (batters) and powerplay, middle and "
         "death bowlers, when the group has at least 8 eligible players."],
        [("Combining filters. ", "b"), "Weighted average of filter scores (All-round). A player missing a filter gets a neutral 50 for "
         "it and needs at least half the total weight covered, so playing fewer contexts cannot help."],
    ])
    fw = cfg["filter_weights"]
    mb = cfg["min_balls"]
    doc.table(["Filter", "Weight", "Min pressure balls (bat)", "Min (bowl)", "Eligible batters", "Eligible bowlers"],
              [[FILTER_LABEL[f], fw[f], mb["bat"][f], mb["bowl"][f], N["eligible"]["bat"].get(f, 0), N["eligible"]["bowl"].get(f, 0)]
               for f in fw], font=9)
    doc.p("Minimums apply to the effective (recency and opposition weighted) sample. Playoffs carry a light weight because the sample is small.")

    # ------------------------------------------------------------ reliability
    doc.h("6. Reliability")
    doc.p("Each check re-runs the exact production engine on perturbed data.")
    doc.h("6.1 Split-half repeatability, and how we improved it", 2)
    doc.p("We split matches into two random halves, score players on each half, and correlate the two rankings (20 splits). "
          "Our first draft, which shrank toward the league average and weighted the three components equally, gave "
          f"{base['bat_rho']:.2f} for batters — close to noise — and {base['bowl_rho']:.2f} for bowlers. Measuring each component "
          "separately showed why: runs vs expected repeats far better than wicket value or win probability added. The table "
          "shows each change in turn.")
    doc.table(["Scoring version", "Batters ρ", "Batters top-10 overlap", "Bowlers ρ", "Bowlers top-10 overlap"],
              [[r["step"], f"{r['bat_rho']:.2f}", r["bat_top10"], f"{r['bowl_rho']:.2f}", r["bowl_top10"]] for r in AB], font=9)
    doc.fig("ablation.png", "Figure 4. Split-half rank correlation for each scoring change.", width=6.0)
    doc.p(f"Halves use half the data, so these are lower bounds; on the full data the Spearman–Brown estimate is "
          f"{2 * SH['bat']['rho'] / (1 + SH['bat']['rho']):.2f} for batters and {2 * SH['bowl']['rho'] / (1 + SH['bowl']['rho']):.2f} for bowlers.")
    doc.h("6.2 Bootstrap rank ranges", 2)
    doc.p(f"We resample matches with replacement {cfg['n_boot']:,} times and re-rank. A player who fails the minimum sample in a "
          "resample takes the worst rank for it, so ranges are conservative. Ranges are in the tables and Figures 1–2.")
    doc.h("6.3 Sensitivity and leave-one-season-out", 2)
    doc.p("We re-rank under five other filter weightings and three minimum-sample levels (×0.75, ×1, ×1.5), and with each season removed.")
    sw = N["sensitivity_by_weights"]
    doc.table(["Weighting (avg of 3 sample cuts)", "Batters surviving (of 10)", "Bowlers surviving (of 10)"],
              [[k, sw["bat"][k], sw["bowl"][k]] for k in sw["bat"]], font=9)
    doc.table(["Season removed", "Batters surviving", "Bowlers surviving"],
              [[k, N["loso"]["bat"][k], N["loso"]["bowl"][k]] for k in N["loso"]["bat"]], font=9)
    doc.fig("stability.png", "Figure 5. Top-10 survivors under other weightings and with each season removed.")
    mc = N["median_check"]
    doc.h("6.4 Median, not only mean", 2)
    doc.p("Besides capping single innings, we ranked every player by the median value of their pressure innings and compared. "
          f"Rank correlation with the score: {mc['bat']['rho_score_vs_median']:.2f} for batters and {mc['bowl']['rho_score_vs_median']:.2f} for bowlers. "
          f"The submitted top 10 sit on average at the {mc['bat']['top10_median_pct_mean']:.0%} (batters) and "
          f"{mc['bowl']['top10_median_pct_mean']:.0%} (bowlers) percentile of that median ranking, so they are not carried by one innings.")
    doc.h("6.5 Choke rate", 2)
    doc.p("Choke rate (share of pressure innings below the player's own ordinary level) is shown beside every score but not "
          "scored: whether a player chokes in one half of their matches barely predicts the other half.")

    # ------------------------------------------------------------ changes, limits, reproduce
    doc.h("7. Changes from the design and why")
    doc.bullets([
        f"Pressure ball threshold moved from the top 20% to the top {round((1 - cfg['pressure_pct']) * 100)}%: the narrower 10% and 20% cuts were less repeatable in split-half tests because samples got too small.",
        "Shrinkage toward the player's own level instead of the league mean, and reliability-based component weights (section 6.1).",
        "Choke rate is reported, not scored, because it does not repeat.",
        "Must-win, rivalry and the rebuilt points table are derived from the match results, as planned, because the data has no points table or rivalry field.",
    ])
    doc.h("8. Limits")
    doc.bullets([
        f"Playoff and must-win samples are small ({D['playoff_matches']} knock-out matches), so those filters carry little weight and rank ranges stay wide.",
        "Skill under pressure beyond a player's normal level is hard to separate from noise in five seasons of data. The score "
        "therefore leans on performance against expectation on pressure balls, with the rise over normal as a smaller part.",
        f"The batter list leans on the latest season: with {max(N['loso']['bat'], key=int)} removed, "
        f"{N['loso']['bat'][max(N['loso']['bat'], key=int)]} of the 10 batters stay. Recent seasons weigh more by design, and several "
        "batters built most of their pressure record recently. The bowler list is steadier.",
        "T20I opposition strength varies; associate games are down-weighted and opposition is adjusted per ball, but not perfectly.",
        "No pitch, weather or player price data, so auction value is not modelled.",
    ])
    doc.h("9. Reproducing the results")
    doc.p("Place the supplied CSV files in data/raw/, then run, in order:")
    for c in ("uv sync", "uv run python -m src.build        # data, win probability, leverage, aggregates",
              "uv run python -m src.reliability  # bootstrap, split-half, sensitivity, leave-one-season-out",
              "uv run python -m src.report       # locked lists, numbers and figures",
              "uv run python -m src.report_doc   # this document",
              "uv run streamlit run app.py       # dashboard"):
        para = doc.p(c, after=0)
        for r in para.runs:
            r.font.name, r.font.size = "Consolas", Pt(9)
    doc.p("Random seeds are fixed, so two runs give identical outputs. All tunable settings are in src/config.py.", after=6)
    if url:
        doc.p("Dashboard: ", (url, "b"))
    DOCX.parent.mkdir(parents=True, exist_ok=True)
    d.save(DOCX)
    print("wrote", DOCX)


if __name__ == "__main__":
    run()
