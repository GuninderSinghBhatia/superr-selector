"""Writes the detailed methodology report reports/SupeRR_Selector_R1_Methodology.docx.

Every number comes from outputs/report_numbers.json, outputs/report_extra.json and the submission CSVs.
Run after `python -m src.report` and `python -m src.report_extra`."""
import json
import os

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from .config import FIG, OUT, ROOT

ROYAL, PINK, INK, MUTED = RGBColor(0x25, 0x4A, 0xA5), RGBColor(0xEA, 0x1A, 0x85), RGBColor(0x0F, 0x1E, 0x4A), RGBColor(0x5A, 0x66, 0x90)
DOCX = ROOT / "reports" / "SupeRR_Selector_R1_Methodology.docx"
REPO = "https://github.com/GuninderSinghBhatia/superr-selector"
FL = {"inn2": "Chasing / defending", "inn1": "First innings", "must_win": "Must-win (IPL)",
      "playoff": "Playoffs (IPL)", "rivalry": "Rivalry (IPL)", "bad_form": "Out of form (IPL)"}
FILTERS = list(FL)


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
        for lvl, size in ((1, 17), (2, 13), (3, 11.5)):
            h = st[f"Heading {lvl}"]
            h.font.name, h.font.size, h.font.color.rgb, h.font.bold = "Cambria", Pt(size), ROYAL, True
        st["Title"].font.name, st["Title"].font.color.rgb, st["Title"].font.size = "Cambria", ROYAL, Pt(30)
        for s in self.d.sections:
            s.left_margin = s.right_margin = Inches(0.9)
            s.top_margin = s.bottom_margin = Inches(0.8)
        self.fig_n = 0
        self.tab_n = 0

    def h(self, text, lvl=1):
        self.d.add_heading(text, lvl)

    def p(self, *runs, style=None, after=6, size=None):
        para = self.d.add_paragraph(style=style)
        for r in runs:
            if isinstance(r, tuple):
                run = para.add_run(r[0])
                run.bold, run.italic = "b" in r[1], "i" in r[1]
            else:
                run = para.add_run(r)
            if size:
                run.font.size = Pt(size)
        para.paragraph_format.space_after = Pt(after)
        return para

    def bullets(self, items):
        for it in items:
            self.p(*(it if isinstance(it, list) else [it]), style="List Bullet", after=2)
        self.d.paragraphs[-1].paragraph_format.space_after = Pt(6)

    def eq(self, text, where=None):
        para = self.d.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = para.add_run(text)
        r.font.name, r.font.size, r.italic = "Cambria Math", Pt(11), True
        para.paragraph_format.space_after = Pt(2 if where else 8)
        if where:
            w = self.p((where, "i"), after=8, size=9.5)
            for run in w.runs:
                run.font.color.rgb = MUTED

    def caption(self, kind, text):
        if kind == "Table":
            self.tab_n += 1
            n = self.tab_n
        else:
            self.fig_n += 1
            n = self.fig_n
        cap = self.p((f"{kind} {n}. ", "b"), (text, "i"), after=10)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in cap.runs:
            r.font.size, r.font.color.rgb = Pt(9), MUTED

    def table(self, header, rows, widths=None, font=9.5, caption=None):
        if caption:
            self.caption("Table", caption)
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
        self.caption("Figure", caption)

    def toc(self):
        para = self.d.add_paragraph()
        r = para.add_run()
        for tag, text in (("begin", None), (None, 'TOC \\o "1-2" \\h \\z \\u'), ("separate", None), (None, None), ("end", None)):
            if tag:
                f = OxmlElement("w:fldChar")
                f.set(qn("w:fldCharType"), tag)
                r._r.append(f)
            elif text:
                it = OxmlElement("w:instrText")
                it.set(qn("xml:space"), "preserve")
                it.text = text
                r._r.append(it)
            else:
                t = OxmlElement("w:t")
                t.text = "Right-click and choose Update Field to build the table of contents."
                r._r.append(t)

    def page_break(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def fname(f):
    """Filter name for running text: lower case, keeping the IPL tag."""
    base = FL[f].replace(" (IPL)", "").lower()
    return base + " (IPL)" if "(IPL)" in FL[f] else base


def pct(x):
    return f"{x:.0%}"


def run():
    N = json.loads((OUT / "report_numbers.json").read_text())
    X = json.loads((OUT / "report_extra.json").read_text())
    lists = {r: pd.read_csv(OUT / f"submission_top10_{n}.csv") for r, n in (("bat", "batters"), ("bowl", "bowlers"))}
    cfg, D, SH, AB = N["config"], N["data"], N["split_half"], N["ablation"]
    base = AB[0]
    url = os.environ.get("DASH_URL", "https://superr-selector-r1.streamlit.app")
    share = round((1 - cfg["pressure_pct"]) * 100)
    lev = round(cfg["leverage_share"] * 100)
    ow, fw, mb, cw = cfg["output_weights"], cfg["filter_weights"], cfg["min_balls"], cfg["component_weights"]
    doc = Doc()
    d = doc.d

    # ================================================================ title
    d.add_paragraph("SupeRR Selector R1", style="Title")
    doc.p(("Rating IPL and T20I players on performance under pressure", "b"), size=15)
    doc.p("Methodology and results · November 2026", after=14)
    doc.p(("Submission. ", "b"), "Top 10 batters and top 10 bowlers, each with a bootstrap rank range and the probability of staying in the top 10.")
    doc.p(("Dashboard. ", "b"), url)
    doc.p(("Code and outputs. ", "b"), REPO)
    doc.p(("Data. ", "b"), f"The supplied files only: {D['matches']} matches ({D['ipl_matches']} IPL), {D['balls']:,} deliveries, {D['seasons']}. "
          "Every number in this report is produced by the same code and tables as the submitted lists and the dashboard.")
    doc.p(("Contents", "b"), size=13, after=4)
    doc.toc()
    doc.page_break()

    # ================================================================ 1 summary
    doc.h("1. Executive summary")
    doc.p("The task is to rank players by how they perform under pressure compared with their usual level. We answer it in four steps.")
    doc.bullets([
        [("Measure pressure on every ball. ", "b"), "Two win-probability models give each side's chance of winning before every ball. "
         "Leverage is how far the next ball can move that chance. Combined with five match signals (dot-ball streaks, recent wickets, a new "
         f"batter at a low score, the required-rate gap, a set batter against a fresh bowler), it forms a pressure index. The top {share}% of balls "
         "in each innings are pressure balls. Four IPL-only context filters (must-win, playoffs, rivalry, out of form) add weight on top."],
        [("Measure performance against expectation. ", "b"), "Each ball's outcome is compared with what the league usually gets from the same "
         "situation, then adjusted for the quality of the opponent on the other side and standardised within IPL and within T20I."],
        [("Compare with the player's own level. ", "b"), "Pressure samples are small, so each player's pressure performance is shrunk toward their "
         "own ordinary-ball level. A difference survives only where the evidence supports it. Scores are 0–100 percentiles within role."],
        [("Show how far to trust each rank. ", "b"), f"{cfg['n_boot']:,} match resamples give every submitted player a rank range and "
         "a probability of staying in the top 10. Split-half, sensitivity and leave-one-season-out checks test the ranking as a whole."],
    ])
    doc.p(("Headline results. ", "b"),
          f"The top-ranked batter is {lists['bat'].Player[0]} and the top-ranked bowler is {lists['bowl'].Player[0]}. "
          f"Scored on two random halves of the matches, players' rankings correlate at {SH['bat']['rho']:.2f} (batters) and {SH['bowl']['rho']:.2f} "
          f"(bowlers), up from {base['bat_rho']:.2f} and {base['bowl_rho']:.2f} for our first draft. Across alternative weightings and "
          f"sample cuts, on average {N['sensitivity_mean_survivors']['bat']} of the 10 batters and {N['sensitivity_mean_survivors']['bowl']} "
          "of the 10 bowlers stay in the top 10. The bowler list is the steadier of the two; the batter list leans on the latest season (section 8.4).")

    # ================================================================ 2 lists
    doc.h("2. The submitted lists")
    hdr = ["#", "Player", "Team", "Role", "Score", "Rank range", "P(top 10)", "Choke", "Pressure balls"]
    w = [0.3, 1.5, 1.45, 0.75, 0.5, 0.75, 0.65, 0.5, 0.65]

    def rows(t):
        return [[r.Rank, r.Player, r.Team if isinstance(r.Team, str) else "", r.Role if isinstance(r.Role, str) else "", f"{r.Score:.1f}",
                 f"{int(r['Rank low (5%)'])}–{int(r['Rank high (95%)'])}", pct(r["P(top 10)"]),
                 f"{r['Choke rate']:.0f}%" if pd.notna(r["Choke rate"]) else "–", int(r["Pressure balls"])] for _, r in t.iterrows()]
    doc.table(hdr, rows(lists["bat"]), w, caption="Top 10 batters under pressure.")
    doc.table(hdr, rows(lists["bowl"]), w, caption="Top 10 bowlers under pressure.")
    doc.p(("Columns. ", "b"), "Score: weighted 0–100 pressure score. Rank range: 5th–95th percentile of the player's rank over "
          f"{cfg['n_boot']:,} resamples of matches; a range ending above 100 means the player sometimes falls below the minimum sample and drops out. "
          "P(top 10): share of resamples in which the player stays in the top 10. Choke: share of the player's pressure innings or spells that "
          "fell below their own ordinary level (shown, not scored; section 7.6). Pressure balls: the sample behind the score. Team: the "
          "player's latest IPL side where they have one. Role: batting position group, or the phase the bowler bowls most.")
    doc.fig("top10_bat.png", "Submitted batters: rank and bootstrap rank range (log scale).")
    doc.fig("top10_bowl.png", "Submitted bowlers: rank and bootstrap rank range (log scale).")

    # ================================================================ 3 framing
    doc.h("3. How we framed the problem")
    doc.p("Three choices shape everything else.")
    doc.bullets([
        [("Pressure belongs to the ball, not the match. ", "b"), "A final has calm overs and a league game has frantic ones. We measure "
         "pressure ball by ball from the match state, then let match context (playoffs, must-win games, rivalries, a player's form) add to it, "
         "never replace it."],
        [("Performance is measured against expectation, not in raw runs or wickets. ", "b"), "A run-a-ball 20 is poor in the powerplay and "
         "excellent when 15 are needed from 6 balls with 8 wickets down. Comparing each ball with the league average for the same situation "
         "makes those two innings comparable."],
        [("\"Usual level\" is the player's own ordinary-ball performance. ", "b"), "Every player has a baseline from their non-pressure balls. "
         "Pressure performance is estimated with that baseline as the starting point, and the score also rewards the rise above it."],
    ])
    doc.p("A fourth principle follows: a rank is only worth submitting with its uncertainty. That drove the reliability work in section 8 "
          "and the rank ranges beside every name.")

    # ================================================================ 4 data
    doc.h("4. Data")
    doc.h("4.1 Files and coverage", 2)
    doc.table(["File", "Used for"], [
        ["ball_by_ball.csv", "Every delivery: runs, extras, wickets and dismissal type, striker, bowler, batting order, pace or spin"],
        ["matches.csv", "Date, competition, stage, knock-out flag, result, winner, revised overs and target"],
        ["playing_eleven.csv", "Checked for roles; batting position is taken from the ball-by-ball file"],
        ["competitions.csv, teams.csv, mapping", "Competition names (IPL or T20I), team names, player ids"],
    ], [1.9, 4.6], caption="Supplied files and how they are used.")
    cov = X["coverage"]["matches_by_season_tier"]
    tiers = ["IPL", "T20I", "T20I-assoc"]
    doc.table(["Season", "IPL", "T20I (full members)", "T20I (associate)", "Total"],
              [[s] + [v.get(t, 0) for t in tiers] + [sum(v.values())] for s, v in sorted(cov.items(), key=lambda kv: int(kv[0]))],
              [1.0, 1.2, 1.6, 1.6, 0.9], caption="Matches by season and tier.")
    doc.h("4.2 Cleaning rules", 2)
    doc.bullets([
        "Super overs are dropped; only innings 1 and 2 are scored.",
        "A legal ball excludes wides and no-balls. A ball the batter faced excludes wides only.",
        "Runs charged to the bowler include wides and no-ball extras, not byes or leg-byes.",
        "Bowler wickets: caught, bowled, LBW, stumped and hit wicket. Run outs count against the batter, not for the bowler. Retired out is not a dismissal.",
        "Rain-affected matches use the revised overs and target where the data has them, so balls left and runs needed are correct.",
        f"Ties ({D['ties']}) and no-results ({D['no_results']}) are excluded when training the win-probability models; no-results add no "
        "result-based credit. Super-over winners get the points in the rebuilt IPL table.",
        "Tiers: IPL; T20I between full members; T20I involving an associate side (weighted ×"
        f"{cfg['associate_weight']}). Emerging-teams events count as T20I.",
    ])

    # ================================================================ 5 pressure
    doc.h("5. Measuring pressure")
    wp = N["wp_metrics"]
    doc.h("5.1 Win probability", 2)
    doc.p("Two gradient-boosted classifiers estimate the batting side's chance of winning before each ball. Both are constrained to be monotonic: "
          "more runs needed or fewer wickets in hand can never raise the chasing side's chance.")
    doc.table(["Model", "Features (monotonic direction)", "Cross-validated AUC", "Brier score", "Balls"], [
        ["Chasing (innings 2)", "runs needed (−), balls left (+), wickets in hand (+), required rate (−), target, IPL flag",
         f"{wp['inn2']['auc']:.3f}", f"{wp['inn2']['brier']:.3f}", f"{wp['inn2']['n']:,}"],
        ["Setting (innings 1)", "score (+), balls left (+), wickets in hand (+), IPL flag; plus one end-of-innings row per match",
         f"{wp['inn1']['auc']:.3f}", f"{wp['inn1']['brier']:.3f}", f"{wp['inn1']['n']:,}"],
    ], [1.2, 2.9, 0.9, 0.7, 0.8], font=9, caption="Win-probability models. Five-fold cross-validation grouped by match, so no match is in both training and test.")
    doc.p("Innings 1 is harder to predict because the chase has not happened yet; an AUC near 0.69 is typical for first-innings models. "
          f"Calibration is close: across probability bands, predicted and actual win rates differ by {X['calibration_gap']:.3f} on average "
          "(Figure 3; measured in-sample, so slightly optimistic).")
    doc.fig("calibration.png", "Predicted win probability against how often the batting side actually won, by band.", width=3.8)
    doc.h("5.2 Leverage", 2)
    doc.p("Leverage is the expected size of the swing in win probability on the next ball:")
    doc.eq("L(s) = Σₒ p(o | innings, phase) · | WP(s after o) − WP(s) |",
           "o runs over the next-ball outcomes {0, 1, 2, 3, 4, 6, wicket, extra}; p(o) is how often each outcome happens in that innings and phase; "
           "s is the match state (score or runs needed, balls left, wickets in hand).")
    doc.p("Read from the batting side this is chasing pressure; read from the bowling side, the same number is defending pressure.")
    doc.h("5.3 First-innings par", 2)
    doc.p("The first innings has no target, so we also measure how far a batting side is behind par. A runs-remaining model (gradient boosting, "
          "monotonic in balls left and wickets in hand, trained on full 20-over first innings) projects the final total from the current state. "
          "The par deficit is the average projection from the same point in the innings minus this side's projection; a positive deficit means "
          "the side is behind, for example after a collapse. The same model prices a wicket in runs:")
    doc.eq("c(s) = R(balls left, wickets in hand) − R(balls left, wickets in hand − 1)",
           "R is the projected runs still to come. Losing a wicket at 30 for 4 costs more future runs than at 180 for 4.")
    doc.h("5.4 Extra signals and the pressure index", 2)
    doc.table(["Signal", "Definition"], [
        ["Dot-ball streak", "Consecutive scoreless balls before this one in the innings"],
        ["Recent wickets", "Wickets in the previous 18 balls"],
        ["New batter at a low score", "Striker has faced under 6 balls, 3+ wickets down, before the 16th over"],
        ["Rate gap", "Innings 2: required rate minus current rate (capped −6 to 12). Innings 1: par deficit"],
        ["Set batter v fresh bowler", "Striker has faced 20+ balls; bowler has bowled under 6 in the innings"],
    ], [1.9, 4.6], caption="Extra pressure signals.")
    doc.eq(f"PI = pct( {cfg['leverage_share']} · pct(L) + {1 - cfg['leverage_share']:.1f} · mean_k pct(signal_k) )",
           "pct( ) is the percentile within innings 1 or within innings 2, so the two innings are on the same footing.")
    doc.p(f"A pressure ball is one with PI ≥ {cfg['pressure_pct']}, the top {share}% of balls in each innings. Leverage carries {lev}% of the index "
          "because it is grounded in the win-probability model; the signals capture strain the model does not see, such as a run of dot balls.")
    sw_rows = X["threshold_sweep"]
    doc.p(("Choosing the threshold. ", "b"), "We rebuilt everything at four thresholds and measured how well each ranking repeats (section 8.1). "
          "Narrower cuts mean more extreme balls but fewer of them, so fewer players reach the minimum sample.")
    doc.table(["Pressure balls", "Batters ρ", "Batters top-10 overlap", "Bowlers ρ", "Bowlers top-10 overlap", "Batters / bowlers ranked in both halves"],
              [[f"Top {round(r['pressure_share'] * 100)}%" + (" (chosen)" if abs(r["pressure_share"] - (1 - cfg["pressure_pct"])) < 1e-9 else ""),
                f"{r['bat_rho']:.2f}", r["bat_top10"], f"{r['bowl_rho']:.2f}", r["bowl_top10"], f"{r['bat_ranked'] // 2} / {r['bowl_ranked'] // 2}"]
               for r in sw_rows], font=9, caption="Split-half repeatability at each pressure threshold (12 random splits each).")
    s20 = next(r for r in sw_rows if abs(r["pressure_share"] - 0.2) < 1e-9)
    s30 = next(r for r in sw_rows if abs(r["pressure_share"] - 0.3) < 1e-9)
    doc.p(f"The top {share}% is the best balance. At 20% bowlers repeat slightly better ({s20['bowl_rho']:.2f} against {s30['bowl_rho']:.2f}), "
          f"but batters fall from {s30['bat_rho']:.2f} to {s20['bat_rho']:.2f} and the pool of ranked batters shrinks by about a third. "
          "At 40% the ranking repeats as well but no longer isolates pressure: four balls in ten would count.")
    doc.fig("pressure_map.png", "Average pressure index by over and wickets down. Pressure peaks when wickets fall early or in clusters, and in the "
            "middle and late overs with four to seven wickets down; a side cruising with wickets in hand sees little.")
    ex = X["worked_example"]
    doc.h("5.5 Worked example", 2)
    doc.p(f"The IPL knock-out chase with the highest average leverage is the {ex['season']} {ex['stage']}, {ex['teams']}. Chasing {ex['target']}, "
          f"the chasing side starts at {ex['start_wp']:.0%} to win, and win probability swings with every wicket and big over. "
          f"{ex['pressure_balls']} of the {ex['balls']} balls are pressure balls, and on the highest-leverage ball the expected swing was "
          f"{ex['max_leverage']:.0%}. Result: {ex['result']}. Every ball in this chase counts towards the chasing / defending and playoff "
          "filters of the players involved, weighted by its leverage.")
    doc.fig("worked_example.png", "Win probability (line) and pressure index (shaded) through the chase. Dots mark wickets.")
    doc.h("5.6 IPL context filters", 2)
    doc.p("The data has no points table or rivalry field, so both are rebuilt from match results.")
    fin_tbl = json.loads((OUT / "build_meta.json").read_text())["finals"]
    doc.bullets([
        [("Must-win. ", "b"), f"We replay every IPL league match in date order to rebuild the table before each game. A top-4 finish needed a median of "
         f"{N['must_win_cutoff']} points in 2022–2025. A game is must-win for a team when losing it would leave them unable to reach "
         f"{N['must_win_cutoff']} even by winning every remaining game, while winning keeps it possible ({D['must_win_team_matches']} team-matches)."],
        [("Playoffs. ", "b"), f"Qualifiers, eliminators and finals, from the knock-out flag ({D['playoff_matches']} IPL matches)."],
        [("Rivalry. ", "b"), "Team pairs with at least 8 meetings, scored half on how even the head-to-head is and half on the share of close finishes: "
         "a margin of 12 runs or less, or a chase won with 6 balls or fewer or 3 wickets or fewer in hand. The top "
         f"{len(D['rivalry_pairs'])} pairs are flagged."],
        [("Out of form. ", "b"), "Going into a match, at least 4 of the player's last 5 innings (4+ balls faced) or spells (12+ balls) were below "
         "their own running average, with at least 10 earlier innings to set that average."],
    ])
    doc.table(["Season", "4th-place points", "5th-place points", "All league games played"],
              [[r["season"], r["fourth_pts"], r["fifth_pts"], "yes" if r["complete"] else "no (washouts)"] for r in fin_tbl],
              [1.0, 1.5, 1.5, 2.0], caption="Rebuilt IPL tables: points needed for the top four.")
    doc.table(["Pair", "Meetings", "Head-to-head (first team's wins)", "Close finishes"],
              [[f"{r['team_a']} v {r['team_b']}", r["meetings"], pct(r["h2h_share_a"]), pct(r["close_share"])] for r in D["rivalry_pairs"]],
              [3.0, 0.9, 1.6, 1.1], caption="Rivalry pairs.")
    mult = ", ".join(f"{FL[k].split(' (')[0].lower()} ×{v}" for k, v in cfg["context_mult"].items())
    doc.p("Context lowers the bar rather than replacing it. A ball in a context match counts for that filter when PI × m ≥ "
          f"{cfg['pressure_pct']}, with m = {mult}. A dead over in a final still does not count, but a moderately tense ball in a final does.")
    doc.h("5.7 Does the definition separate pressure from ordinary play?", 2)
    V = {(r["innings"], r["phase"], r["pressure"]): r for r in N["validation"]}
    ph = ("powerplay", "middle", "death")
    more_dots = sum(V[(i, p, "pressure")]["dot_pct"] > V[(i, p, "ordinary")]["dot_pct"] for i in (1, 2) for p in ph)
    lower_rr = sum(V[(i, p, "pressure")]["run_rate"] < V[(i, p, "ordinary")]["run_rate"] for i in (1, 2) for p in ph)
    d2p, d2o = V[(2, "death", "pressure")], V[(2, "death", "ordinary")]
    doc.p(f"Within the same innings and phase, pressure balls go for fewer runs in {lower_rr} of 6 phases and bring more dots in {more_dots} of 6. "
          f"The exception is the end of a chase: needing a big finish, batters swing, so death-over pressure balls in innings 2 go at {d2p['run_rate']:.1f} "
          f"an over against {d2o['run_rate']:.1f}, and wickets rise ({d2p['wicket_pct']:.1f}% against {d2o['wicket_pct']:.1f}%). In the first innings "
          "pressure shows up as caution rather than wickets. Because pressure changes what a normal outcome looks like, performance is "
          "always judged against the expectation for the situation, not against raw averages.")
    doc.fig("pressure_validation.png", "Dot-ball and boundary rates on ordinary and pressure balls, by innings and phase.")
    doc.table(["Innings", "Phase", "Ball type", "Balls", "Run rate", "Wicket %", "Dot %", "Boundary %"],
              [[r["innings"], r["phase"], r["pressure"], f"{r['balls']:,}", f"{r['run_rate']:.2f}", f"{r['wicket_pct']:.2f}",
                f"{r['dot_pct']:.1f}", f"{r['boundary_pct']:.1f}"] for r in N["validation"]], font=9,
              caption="Pressure against ordinary balls in the same innings and phase.")

    # ================================================================ 6 performance
    doc.h("6. Measuring performance on each ball")
    doc.h("6.1 Expected values", 2)
    doc.p("For every ball we look up the league average for the same situation, defined by six keys: competition group (IPL or T20I), innings, "
          "phase (overs 1–6, 7–15, 16–20), pace or spin, wickets in hand (1–4, 5–7, 8–10) and the striker's batting position "
          "(openers 1–2, middle order 3–5, finishers 6–11). This gives expected batter runs xR, expected dismissal probability xW, "
          "expected runs conceded xRc and expected bowler-wicket probability xBW.")
    doc.h("6.2 Opposition adjustment", 2)
    doc.p("A batter facing a strong bowler should be expected to score less. We estimate each bowler's effect on batters, and each batter's "
          "effect on bowlers, as a shrunk average residual and add it to the expectation:")
    doc.eq("xR_adj = xR + Σ (runs − xR) over the bowler's balls / (n_bowler + 150)",
           "The +150 balls (+300 for wickets) pull players with little data toward zero effect. The same form adjusts xW, xRc and xBW.")
    doc.h("6.3 Three value components", 2)
    doc.table(["Component", "Batter, per ball faced", "Bowler, per ball bowled"], [
        ["Runs vs expected (sr)", "runs − xR_adj", "xRc_adj − runs conceded"],
        ["Wicket value (wk)", "− c(s) · (out − xW_adj)", "c(s) · (wicket × 1.25 if set batter − xBW_adj)"],
        ["Win probability added (wpa)", "WP after − WP before (batting side)", "−(WP after − WP before)"],
    ], [1.7, 2.4, 2.4], caption="Value components. c(s) is the runs a wicket costs from that state; a set batter has faced 15+ balls.")
    doc.h("6.4 Making balls comparable", 2)
    doc.bullets([
        [("Standardised by competition. ", "b"), "Each component is divided by its weighted standard deviation within IPL and within T20I, so a "
         "unit of value means the same in both."],
        [("Weights. ", "b"), f"Each ball carries a recency weight of {cfg['recency_decay']}^(2026 − season) and ×{cfg['associate_weight']} "
         "for T20Is involving an associate side. Pressure balls are also weighted by their leverage relative to a typical pressure ball, capped at 0.5–3×."],
        [("Outliers capped. ", "b"), f"Each player-match average is capped at the {cfg['winsor_pct']:.0%}–{1 - cfg['winsor_pct']:.0%} quantiles for its "
         "role and filter, so one freak innings or spell cannot carry a player."],
    ])

    # ================================================================ 7 scoring
    doc.h("7. From performance to a 0–100 score")
    doc.h("7.1 Samples and eligibility", 2)
    doc.p("Values are summed per player, match and filter, so any season range or bootstrap resample is a re-sum of the same table. A player is "
          "ranked in a filter only with enough pressure balls, counted on the weighted (effective) sample.")
    doc.table(["Filter", "Weight", "Min balls (batters)", "Min balls (bowlers)", "Eligible batters", "Eligible bowlers"],
              [[FL[f], fw[f], mb["bat"][f], mb["bowl"][f], N["eligible"]["bat"].get(f, 0), N["eligible"]["bowl"].get(f, 0)] for f in FILTERS],
              font=9, caption="Filters: submission weight, minimum pressure balls and the number of players who qualify.")
    doc.h("7.2 Shrinkage toward the player's own level", 2)
    doc.p("A player with 80 pressure balls has a noisy pressure average. The best estimate of their true pressure level starts from how they "
          "usually play. For each component and filter, empirical Bayes shrinks the pressure average toward the player's ordinary-ball level:")
    doc.eq("θ̂ = μ_own + (x̄ − μ_own) · τ² / (τ² + se²)",
           "x̄: weighted pressure average; μ_own: the player's ordinary-ball level (itself shrunk toward the league mean); se²: sampling variance "
           "from the pooled within-player spread and the effective sample n_eff = (Σw)²/Σw²; τ²: how much true pressure levels differ from "
           "ordinary levels across players (method of moments, floored at 5% of the observed variance).")
    doc.p("A difference from usual therefore needs evidence to survive: with few balls the estimate stays near the player's normal level, and "
          f"with many it follows what they actually did. For batters this lifted split-half repeatability from {AB[0]['bat_rho']:.2f} to "
          f"{AB[1]['bat_rho']:.2f}; for bowlers it made little difference ({AB[0]['bowl_rho']:.2f} to {AB[1]['bowl_rho']:.2f}). See section 8.1.")
    doc.h("7.3 Weighting the components by how well they repeat", 2)
    doc.p("We measured how well each component repeats between two random halves of the matches, for players with 150+ balls in each half.")
    doc.table(["Role", "Balls", "Players", "Runs vs expected", "Wicket value", "Win prob. added"],
              [["Batters" if r["role"] == "bat" else "Bowlers", r["balls"], r["players"], f"{r['sr']:.2f}", f"{r['wk']:.2f}", f"{r['wpa']:.2f}"]
               for r in X["component_repeatability"]], font=9, caption="Split-half rank correlation of each component (10 random splits).")
    doc.p("Runs against expectation is the most repeatable signal for both roles. Wickets and win probability added are driven by a handful "
          f"of events, so they repeat poorly. The output score therefore weights runs : wickets : win probability {ow['bat']['sr']} : {ow['bat']['wk']} : "
          f"{ow['bat']['wpa']} for batters and {ow['bowl']['sr']} : {ow['bowl']['wk']} : {ow['bowl']['wpa']} for bowlers. Wickets keep a real share, "
          "larger for bowlers, because taking them under pressure is central to the bowling job.")
    doc.h("7.4 Score per filter", 2)
    doc.eq(f"Score_f = 100 · [ {cw['output']} · Σ_c a_c · pct_role(θ̂_c) / Σ_c a_c  +  {cw['rise']} · pct_role(rise) ]",
           "a_c: component weights above; rise: the shrunk gap between the player's pressure and ordinary value; pct_role: percentile among eligible "
           "players of the same role in that filter.")
    doc.p("Percentiles are taken within role (openers, middle order, finishers; powerplay, middle and death bowlers) when the group has at least "
          "8 eligible players, so a finisher is compared with finishers, whose situations differ from an opener's.")
    doc.h("7.5 Combining filters", 2)
    doc.p("The overall score is the weighted average of the filter scores (All-round mode). A player who is not eligible in a filter gets a "
          "neutral 50 for it and must be eligible in filters carrying at least half the total weight, so playing in fewer contexts can neither "
          "help nor sink a player. In the dashboard's Specialist mode the overall score is the player's best selected filter instead.")
    doc.p(f"Submission weights: chasing/defending {fw['inn2']}, first innings {fw['inn1']}, playoffs {fw['playoff']}, must-win {fw['must_win']}, "
          f"out of form {fw['bad_form']}, rivalry {fw['rivalry']}. The two core filters, which use IPL and T20I and have the largest samples, carry "
          f"{fw['inn1'] + fw['inn2']:.0%} of the weight. Playoffs get the largest IPL-only weight because they are the clearest pressure context, "
          "kept modest because the sample is small. Section 8.3 shows how the lists change under other weightings.")
    doc.h("7.6 Choke rate", 2)
    doc.p("A pressure innings is a match where the player had at least 6 pressure balls in a filter. It is a choke when the player's average value on "
          "those balls is below their own ordinary-ball level. Choke rate is shown beside every score but is not part of it: whether a player "
          "chokes in one half of their matches barely predicts the other half, so scoring it would add noise.")

    # ================================================================ 8 reliability
    doc.h("8. Reliability")
    doc.p("Every check below re-runs the production scoring engine on perturbed data; nothing is re-implemented.")
    doc.h("8.1 Split-half repeatability and how we improved it", 2)
    doc.p("Split matches into two random halves, score players on each, and correlate the rankings (20 splits, minimum samples halved). "
          "The table shows our first draft and each change in turn.")
    doc.table(["Scoring version", "Batters ρ", "Batters top-10 overlap", "Bowlers ρ", "Bowlers top-10 overlap"],
              [[r["step"], f"{r['bat_rho']:.2f}", r["bat_top10"], f"{r['bowl_rho']:.2f}", r["bowl_top10"]] for r in AB], font=9,
              caption="Split-half repeatability of each scoring version.")
    doc.fig("ablation.png", "Split-half rank correlation for each scoring change.", width=6.0)
    doc.p(f"Each half has half the data, so these are lower bounds. The Spearman–Brown estimate for the full data is "
          f"{2 * SH['bat']['rho'] / (1 + SH['bat']['rho']):.2f} for batters and {2 * SH['bowl']['rho'] / (1 + SH['bowl']['rho']):.2f} for bowlers. "
          "The top-10 overlap between halves stays modest, which is why we report rank ranges rather than claiming exact positions.")
    doc.h("8.2 Bootstrap rank ranges", 2)
    doc.p(f"We resample matches with replacement {cfg['n_boot']:,} times and re-rank each time. A player who falls below the minimum sample in a "
          "resample takes the worst rank for it, so ranges are conservative. The rank range is the 5th–95th percentile; P(top 10) is the share of "
          "resamples in the top 10.")
    doc.h("8.3 Sensitivity to weights and samples", 2)
    swt = N["sensitivity_by_weights"]
    doc.table(["Weighting (average over 3 sample cuts)", "Batters still top 10", "Bowlers still top 10"],
              [[k, swt["bat"][k], swt["bowl"][k]] for k in swt["bat"]], [3.2, 1.5, 1.5], font=9,
              caption="Submitted players who stay in the top 10 under other weightings, at minimum samples ×0.75, ×1 and ×1.5.")
    doc.h("8.4 Leave one season out", 2)
    doc.table(["Season removed", "Batters still top 10", "Bowlers still top 10"],
              [[k, N["loso"]["bat"][k], N["loso"]["bowl"][k]] for k in N["loso"]["bat"]], [2.0, 1.5, 1.5], font=9,
              caption="Submitted players who stay in the top 10 with each season removed.")
    doc.fig("stability.png", "Top-10 survivors under other weightings (left) and with each season removed (right).")
    last = max(N["loso"]["bat"], key=int)
    doc.p(f"The bowler list holds up across seasons. The batter list depends most on {last}: without it, {N['loso']['bat'][last]} of the 10 batters "
          "stay. Recent seasons weigh more by design, and several batters built most of their pressure record recently. We keep the recency "
          "weighting because the task is to rate players as they are now, and flag the dependence here.")
    mc = N["median_check"]
    doc.h("8.5 Median, not only mean", 2)
    doc.p("Besides capping single innings, we ranked every player by the median value of their pressure innings. That ranking correlates with the "
          f"score at {mc['bat']['rho_score_vs_median']:.2f} (batters) and {mc['bowl']['rho_score_vs_median']:.2f} (bowlers). The submitted players sit "
          f"on average at the {mc['bat']['top10_median_pct_mean']:.0%} and {mc['bowl']['top10_median_pct_mean']:.0%} percentile of the median ranking: "
          "they are consistently good under pressure, not carried by one innings.")

    # ================================================================ 9 results
    doc.h("9. Results in detail")
    doc.h("9.1 Filter scores of the submitted players", 2)
    for role, label in (("bat", "batters"), ("bowl", "bowlers")):
        t = lists[role]
        doc.table(["#", "Player"] + [FL[f].replace(" (IPL)", "*") for f in FILTERS] + ["Overall"],
                  [[r.Rank, r.Player] + [f"{r[f'score_{f}']:.0f}" if pd.notna(r[f"score_{f}"]) else "–" for f in FILTERS] + [f"{r.Score:.1f}"]
                   for _, r in t.iterrows()], [0.3, 1.5, 0.75, 0.7, 0.7, 0.7, 0.7, 0.75, 0.6], font=8.5,
                  caption=f"Filter scores (0–100) of the submitted {label}. * IPL only. – means too few pressure balls to score that filter.")
    doc.h("9.2 Why each player ranks", 2)
    stab = N["top10_stability"]
    for role, label in (("bat", "Batters"), ("bowl", "Bowlers")):
        doc.h(label, 3)
        items = []
        for _, r in lists[role].iterrows():
            sc = {f: r[f"score_{f}"] for f in FILTERS if pd.notna(r[f"score_{f}"])}
            best, low = max(sc, key=sc.get), min(sc, key=sc.get)
            st = stab[role].get(str(int(r.player_id)))
            team = r.Team if isinstance(r.Team, str) else ""
            items.append([(f"{r.Rank}. {r.Player}", "b"),
                          f" ({team}, {r.Role}). Strongest in {fname(best)} ({sc[best]:.0f}), weakest in {fname(low)} ({sc[low]:.0f}); "
                          f"{int(r['Pressure balls'])} pressure balls across {int(r['Filters scored'])} filters. "
                          f"Top 10 in {pct(r['P(top 10)'])} of resamples"
                          + (f" and {pct(st)} of alternative weightings." if st is not None else ".")])
        doc.bullets(items)
    doc.h("9.3 Near misses", 2)
    nm = X["near_misses"]
    doc.table(["Rank", "Batter", "Rank range", "P(top 10)", "Rank", "Bowler", "Rank range", "P(top 10)"],
              [[a["rank"], a["player"], a["range"], pct(a["p_top10"]), b["rank"], b["player"], b["range"], pct(b["p_top10"])]
               for a, b in zip(nm["bat"], nm["bowl"])], [0.45, 1.35, 0.7, 0.7, 0.45, 1.45, 0.7, 0.7], font=8.5,
              caption="Players ranked 11–15.")
    doc.p("Some near misses have a higher chance of a top-10 place than players ranked 8–10. The rank range and P(top 10) are the fairer "
          "reading of the boundary: positions 8 to 15 are close to interchangeable on this data.")
    doc.h("9.4 What the lists say", 2)
    doc.bullets([
        "The bowler list is led by players who keep conceding below expectation when the match is tight, the most repeatable signal and the one the "
        "score leans on. Spinners and new-ball bowlers both feature because each is compared within their own phase.",
        "Middle-order batters make up most of the batter list. Within-role percentiles lift the best opener and the best finishers without "
        "letting any one group crowd the list.",
        f"Uncertainty is real. {int((lists['bat']['P(top 10)'] >= 0.5).sum())} batters and {int((lists['bowl']['P(top 10)'] >= 0.5).sum())} bowlers "
        "are in the top 10 in more than half of the resamples. We submit the most likely top 10 and show the rest of the picture beside it.",
    ])

    # ================================================================ 10-13
    doc.h("10. The dashboard")
    doc.p(f"{url} reads the same per-match table as this report, so every view responds instantly, and its submission setup returns exactly the lists above.")
    doc.bullets([
        "Controls: batters or bowlers; any set of filters, each with a weight; All-round or Specialist mode; season range; minimum-sample multiplier.",
        "Top 10 as cards or a table, with score, rank range, choke rate and pressure balls; CSV export of Rank 1–10.",
        "Pressure profile radar across all six filters for one or more players.",
        "Normal against pressure scatter with four quadrants: Ice (good in both), Fire (better under pressure), Choker (worse under pressure), "
        "Passenger (good normally, not under pressure).",
        "Pressure twins: the players with the most similar filter profile.",
        "Pressure replay: ball-by-ball win probability and pressure through any innings.",
        "Method and reliability tab with the checks in section 8.",
    ])
    doc.h("11. Decisions and alternatives")
    doc.table(["Decision", "Choice", "Alternative considered", "Why"], [
        ["Pressure unit", "Each ball, from win-probability leverage", "Whole matches (finals, close games)", "Calm overs in big games and tense overs in small ones are both common"],
        ["Pressure share", f"Top {share}%", "10%, 20%, 40%", "Best balance of repeatability and sample (section 5.4)"],
        ["Context filters", "Lower the bar (multiplier)", "Count every ball in the match", "A dead over in a final is not pressure"],
        ["Performance", "Above expectation, opposition-adjusted", "Raw runs, strike rate, wickets", "Comparable across phases, roles and opponents"],
        ["Prior", "Player's own ordinary level", "League average", f"Matches 'usual level'; batter repeatability {AB[0]['bat_rho']:.2f} → {AB[1]['bat_rho']:.2f}"],
        ["Components", "Runs-led weights", "Equal weights", "Runs repeat far better (section 7.3)"],
        ["Comparison group", "Within role", "All players together", "Openers, finishers and death bowlers face different situations"],
        ["Choke rate", "Shown, not scored", "Part of the score", "Does not repeat between halves"],
        ["Rivalry, must-win", "Derived from results", "External lists", "No outside data; every flag traces to the supplied files"],
    ], [1.15, 1.55, 1.55, 2.25], font=8.5, caption="Main decisions.")
    doc.h("12. Limitations")
    doc.bullets([
        f"Playoff and must-win samples are small ({D['playoff_matches']} knock-out matches), so those filters carry little weight and rank ranges stay wide.",
        "Skill under pressure beyond a player's normal level is hard to separate from noise in five seasons. The score leans on performance "
        "against expectation on pressure balls, with the rise over normal as a smaller part.",
        "The batter list depends on the latest season (section 8.4).",
        "Opposition adjustment uses a single average effect per player, not matchups (for example left-arm spin against a particular batter).",
        "T20I opposition strength varies; associate games are down-weighted and opposition is adjusted ball by ball, but not perfectly.",
        "No pitch, weather, venue-condition or player-price data, so conditions and auction value are not modelled.",
    ])
    doc.h("13. Reproducing the results")
    doc.p("Place the supplied CSV files in data/raw/ and run:")
    for c in ("uv sync",
              "uv run python -m src.build          # data, win probability, leverage, pressure index, aggregates",
              "uv run python -m src.reliability    # bootstrap, split-half, sensitivity, leave-one-season-out",
              "uv run python -m src.report         # locked lists, numbers and figures",
              "uv run python -m src.report_extra   # threshold sweep, calibration, worked example, near misses",
              "uv run python -m src.report_doc     # this document",
              "uv run streamlit run app.py         # dashboard"):
        para = doc.p(c, after=0)
        for r in para.runs:
            r.font.name, r.font.size = "Consolas", Pt(8.5)
    doc.p("", after=4)
    doc.p("All random seeds are fixed, so two runs give byte-identical outputs. Every tunable setting is in src/config.py (Appendix B).")

    doc.h("Appendix A. Glossary")
    doc.table(["Term", "Meaning"], [
        ["Leverage", "Expected swing in win probability on the next ball"],
        ["Pressure index (PI)", f"Percentile mix of leverage ({lev}%) and five match signals ({100 - lev}%), within each innings"],
        ["Pressure ball", f"A ball in the top {share}% of PI; in a context match, PI × multiplier clears the same bar"],
        ["Expected value", "League average outcome for the same competition, innings, phase, pace/spin, wickets in hand and batting position"],
        ["Usual level", "The player's value on ordinary (non-pressure) balls"],
        ["Rise", "Shrunk difference between a player's pressure and ordinary value"],
        ["Rank range", "5th–95th percentile of rank over match resamples"],
        ["P(top 10)", "Share of resamples in which the player ranks in the top 10"],
        ["Choke rate", "Share of pressure innings below the player's own ordinary level"],
        ["Split-half ρ", "Rank correlation between scores from two random halves of the matches"],
    ], [1.6, 4.9], font=9, caption="Glossary.")
    doc.h("Appendix B. Settings")
    doc.table(["Setting", "Value"], [
        ["Pressure ball threshold (PI percentile)", cfg["pressure_pct"]],
        ["Leverage share of PI", cfg["leverage_share"]],
        ["Context multipliers", ", ".join(f"{k} {v}" for k, v in cfg["context_mult"].items())],
        ["Filter weights", ", ".join(f"{k} {v}" for k, v in fw.items())],
        ["Output vs rise", f"{cw['output']} / {cw['rise']}"],
        ["Component weights (sr / wk / wpa)", f"batters {ow['bat']['sr']}/{ow['bat']['wk']}/{ow['bat']['wpa']}, bowlers {ow['bowl']['sr']}/{ow['bowl']['wk']}/{ow['bowl']['wpa']}"],
        ["Minimum pressure balls, batters", ", ".join(f"{k} {v}" for k, v in mb["bat"].items())],
        ["Minimum pressure balls, bowlers", ", ".join(f"{k} {v}" for k, v in mb["bowl"].items())],
        ["Recency decay per season", cfg["recency_decay"]],
        ["Associate-team weight", cfg["associate_weight"]],
        ["Outlier cap (quantile)", cfg["winsor_pct"]],
        ["Bootstrap resamples", cfg["n_boot"]],
    ], [2.6, 3.9], font=9, caption="Settings used for the submission (src/config.py).")

    DOCX.parent.mkdir(parents=True, exist_ok=True)
    d.save(DOCX)
    print("wrote", DOCX)


if __name__ == "__main__":
    run()
