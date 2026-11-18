// Builds reports/SupeRR_Selector_R1.pptx from outputs/report_numbers.json (run: node reports/build_deck.js)
// Needs pptxgenjs: set NODE_PATH to a node_modules folder that has it, or `npm install pptxgenjs@3.12.0`.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const N = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "report_numbers.json"), "utf8"));
const OUTFILE = path.join(ROOT, "reports", "SupeRR_Selector_R1.pptx");
const DASH_URL = process.env.DASH_URL || "";

const HEX = { royal: "254AA5", pink: "EA1A85", ink: "0F1E4A", muted: "5A6690", grey: "A3ACC9", tint: "FDEAF3",
  tintBlue: "E6ECFA", white: "FFFFFF", line: "F1D6E4", gold: "E9A400" };
const THEME = { name: "SupeRR Royal", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: HEX.ink, lt1: HEX.white, dk2: HEX.royal, lt2: HEX.tint, accent1: HEX.pink, accent2: HEX.royal,
    accent3: HEX.gold, accent4: "7A5AF8", accent5: "0E9F8E", accent6: HEX.grey, hlink: HEX.royal, folHlink: HEX.pink } };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.title = "SupeRR Selector R1 — Pressure ratings";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({ title: "DARK", background: { color: HEX.royal },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.5, fontSize: 40, bold: true,
      color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.15, w: 8.8, h: 1.2, fontSize: 18,
      color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: HEX.white },
  slideNumber: { x: 9.2, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: HEX.muted, fontFace: THEME.bodyFontFace },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.35, w: 9.0, h: 0.65, fontSize: 24, bold: true,
      color: C.text2, fontFace: THEME.headFontFace, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "SupeRR Selector R1", options: { x: 0.5, y: 5.2, w: 4, h: 0.3, fontSize: 10, color: HEX.muted,
      fontFace: THEME.bodyFontFace, margin: 0 } } },
  ] });

const SECTIONS = [];
function section(t) { pres.addSection({ title: t }); SECTIONS.push(t); }
function slide(master, sec) { return pres.addSlide({ masterName: master, sectionTitle: sec }); }
function tb(s, text, o) { s.addText(text, Object.assign({ isTextBox: true, fontFace: THEME.bodyFontFace, color: C.text1, margin: 0 }, o)); }
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill || HEX.tint },
    line: { color: fill || HEX.tint }, objectName: name });
}
const chartText = { catAxisLabelColor: HEX.ink, valAxisLabelColor: HEX.ink, catAxisLabelFontFace: "+mn-lt",
  valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, dataLabelFontFace: "+mn-lt",
  dataLabelFontSize: 9, dataLabelColor: HEX.ink, legendFontFace: "+mn-lt", legendFontSize: 10, legendColor: HEX.ink,
  titleFontFace: "+mn-lt", titleColor: HEX.ink, titleFontSize: 12 };

const L = N.lists, SH = N.split_half, AB = N.ablation;
const base = AB[0], fin = AB[AB.length - 1];
const nBoot = N.config.n_boot.toLocaleString("en-US");

// ---------------------------------------------------------------- 1. title
section("Answer");
let s = slide("DARK", "Answer");
s.addText("Who rises when the match is on the line", { placeholder: "title" });
s.addText(`Pressure ratings for every IPL and T20I player, ${N.data.seasons}. Top 10 batters and bowlers, each with its own reliability evidence.`, { placeholder: "body" });
tb(s, "SupeRR Selector · Round 1", { x: 0.6, y: 0.5, w: 6, h: 0.4, fontSize: 14, color: HEX.tint, bold: true });
s.addNotes("We rate players on how they perform when a ball can swing the match, measured against what that situation usually yields and against the player's own usual level. Every rank comes with how far to trust it.");

// ---------------------------------------------------------------- 2-3. the lists
function listSlide(role, label) {
  const t = L[role];
  const sl = slide("CONTENT", "Answer");
  sl.addText(`Top 10 ${label} under pressure`, { placeholder: "title" });
  const hdr = ["#", "Player", "Team", "Role", "Score", "Rank range", "P(top 10)"].map((h) => ({ text: h,
    options: { bold: true, color: HEX.white, fill: { color: HEX.royal }, fontSize: 11 } }));
  const rows = [hdr];
  t.forEach((r, i) => {
    const fill = { color: i % 2 ? HEX.white : HEX.tint };
    const o = { fontSize: 11, color: HEX.ink, fill };
    rows.push([
      { text: String(r.Rank), options: Object.assign({}, o, { bold: true, color: HEX.pink }) },
      { text: r.Player, options: Object.assign({}, o, { bold: true }) },
      { text: r.Team || "", options: o },
      { text: r.Role || "", options: o },
      { text: r.Score.toFixed(1), options: o },
      { text: `${r["Rank low (5%)"]}–${r["Rank high (95%)"]}`, options: o },
      { text: `${Math.round(r["P(top 10)"] * 100)}%`, options: o },
    ]);
  });
  sl.addTable(rows, { x: 0.5, y: 1.15, w: 9.0, colW: [0.4, 2.2, 2.3, 0.9, 0.7, 1.2, 1.3], rowH: 0.3,
    fontFace: THEME.bodyFontFace, border: { type: "none" }, valign: "middle", margin: [0, 0.06, 0, 0.06], objectName: `${role}-table` });
  tb(sl, `Rank range = 5th–95th percentile of rank over ${nBoot} match resamples. P(top 10) = share of resamples in which the player stays top 10.`,
    { x: 0.5, y: 4.6, w: 8.5, h: 0.45, fontSize: 10, color: HEX.muted });
  sl.addNotes(`The submitted ${label} list. Scores are 0-100 percentiles within role. The range column is the honest part: it shows how much each rank could move if the matches had fallen differently.`);
}
listSlide("bat", "batters");
listSlide("bowl", "bowlers");

// ---------------------------------------------------------------- 4. what pressure is
section("Method");
s = slide("CONTENT", "Method");
s.addText("Pressure = how far the next ball can swing the match", { placeholder: "title" });
const pctTop = Math.round((1 - N.config.pressure_pct) * 100);
const cards = [
  ["Chasing and defending", "Win probability from runs needed, balls left and wickets in hand. Leverage = expected swing of the next ball.", "IPL + T20I"],
  ["First innings", "Projected score vs par for the same balls left and wickets in hand. Behind par with wickets down = pressure.", "IPL + T20I"],
  ["Match context", "Must-win (rebuilt points table), playoffs, rivalries (even head-to-head, close finishes), out-of-form player.", "IPL only"],
];
cards.forEach(([h, b, tag], i) => {
  const x = 0.5 + i * 3.05;
  card(s, x, 1.25, 2.85, 2.1, i === 2 ? HEX.tintBlue : HEX.tint, `card-${i}`);
  tb(s, tag, { x: x + 0.2, y: 1.4, w: 2.4, h: 0.3, fontSize: 10, bold: true, color: i === 2 ? HEX.royal : HEX.pink });
  tb(s, h, { x: x + 0.2, y: 1.7, w: 2.5, h: 0.45, fontSize: 16, bold: true, fontFace: THEME.headFontFace });
  tb(s, b, { x: x + 0.2, y: 2.2, w: 2.5, h: 1.5, fontSize: 12, valign: "top" });
});
tb(s, [{ text: `Top ${pctTop}%`, options: { bold: true, color: HEX.pink, fontSize: 22, fontFace: THEME.headFontFace } },
  { text: `  of balls by pressure index = a pressure ball. Index = ${Math.round(N.config.leverage_share * 100)}% leverage + ${Math.round((1 - N.config.leverage_share) * 100)}% extra signals (dot-ball streak, recent wickets, new batter at a low score, rate gap, set batter vs fresh bowler).`, options: { fontSize: 12 } }],
  { x: 0.5, y: 3.65, w: 9.0, h: 0.9, valign: "middle" });
s.addNotes(`Win-probability models: chasing AUC ${N.wp_metrics.inn2.auc.toFixed(2)}, first innings AUC ${N.wp_metrics.inn1.auc.toFixed(2)}, cross-validated by match. Context filters lower the leverage bar instead of replacing it, so a quiet over in a final does not count by itself.`);

// ---------------------------------------------------------------- 5. validation
s = slide("CONTENT", "Method");
const V = N.validation;
const cats = [], ord = [], prs = [];
let moreDots = 0;
[1, 2].forEach((inn) => ["powerplay", "middle", "death"].forEach((ph) => {
  const o = V.find((r) => r.innings === inn && r.phase === ph && r.pressure === "ordinary");
  const p = V.find((r) => r.innings === inn && r.phase === ph && r.pressure === "pressure");
  cats.push(`Inn ${inn} ${ph}`); ord.push(+o.dot_pct.toFixed(1)); prs.push(+p.dot_pct.toFixed(1));
  if (p.dot_pct > o.dot_pct) moreDots += 1;
}));
s.addText(`Pressure balls bring more dots in ${moreDots} of 6 phases`, { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Ordinary balls", labels: cats, values: ord }, { name: "Pressure balls", labels: cats, values: prs }],
  Object.assign({ x: 0.5, y: 1.15, w: 5.9, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: [HEX.grey, HEX.pink],
    showValue: true, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", valAxisMinVal: 0,
    valGridLine: { color: "EEE3EA", size: 0.5 }, catGridLine: { style: "none" }, showTitle: true, title: "Dot-ball % by phase",
    objectName: "validation-chart" }, chartText));
const i2d = V.find((r) => r.innings === 2 && r.phase === "death" && r.pressure === "pressure");
const i2o = V.find((r) => r.innings === 2 && r.phase === "death" && r.pressure === "ordinary");
card(s, 6.7, 1.25, 2.8, 3.6, HEX.tintBlue, "validation-note");
tb(s, "What the check shows", { x: 6.9, y: 1.4, w: 2.4, h: 0.4, fontSize: 15, bold: true, fontFace: THEME.headFontFace, color: HEX.royal });
tb(s, [
  { text: "Scoring falls on pressure balls in most phases: fewer boundaries, more dots.", options: { bullet: { indent: 14 }, breakLine: true } },
  { text: `Exception: death overs of a chase run at ${i2d.run_rate.toFixed(1)} vs ${i2o.run_rate.toFixed(1)} an over — batters must swing, and wickets rise (${i2d.wicket_pct.toFixed(1)}% vs ${i2o.wicket_pct.toFixed(1)}%).`, options: { bullet: { indent: 14 }, breakLine: true } },
  { text: "First-innings pressure shows up as caution, not wickets.", options: { bullet: { indent: 14 } } },
], { x: 6.9, y: 1.85, w: 2.45, h: 2.9, fontSize: 12, valign: "top", paraSpaceAfter: 6 });

// ---------------------------------------------------------------- 6. how a score is built
s = slide("CONTENT", "Method");
s.addText("Each ball is scored against what its situation usually yields", { placeholder: "title" });
const steps = [
  ["1", "Expected value", "League average for innings, phase, pace/spin, wickets in hand, batting position"],
  ["2", "Opposition", "Adjusted for the quality of the bowler or batter on the other side"],
  ["3", "Standardise", "Within IPL and within T20I; one huge innings capped (2nd–98th pct)"],
  ["4", "Shrink", "Toward the player's own usual level: a gap survives only with evidence"],
  ["5", "Percentile", "0–100 within role, per filter; filters combined by weight"],
];
steps.forEach(([n, h, b], i) => {
  const x = 0.5 + i * 1.84;
  s.addShape(pres.shapes.OVAL, { x: x + 0.55, y: 1.3, w: 0.6, h: 0.6, fill: { color: i === 3 ? HEX.pink : HEX.royal }, line: { color: i === 3 ? HEX.pink : HEX.royal }, objectName: `step-dot-${n}` });
  tb(s, n, { x: x + 0.55, y: 1.3, w: 0.6, h: 0.6, fontSize: 18, bold: true, color: HEX.white, align: "center", valign: "middle" });
  tb(s, h, { x, y: 2.05, w: 1.7, h: 0.4, fontSize: 15, bold: true, align: "center", fontFace: THEME.headFontFace });
  tb(s, b, { x, y: 2.5, w: 1.7, h: 1.3, fontSize: 12, align: "center", valign: "top", color: HEX.muted });
});
const ow = N.config.output_weights, fw = N.config.filter_weights;
card(s, 0.5, 3.95, 9.0, 0.95, HEX.tint, "weights-card");
tb(s, [
  { text: "Score = ", options: { bold: true } },
  { text: `${Math.round(N.config.component_weights.output * 100)}% output + ${Math.round(N.config.component_weights.rise * 100)}% rise over own baseline. Output: batters ${ow.bat.sr}/${ow.bat.wk}/${ow.bat.wpa}, bowlers ${ow.bowl.sr}/${ow.bowl.wk}/${ow.bowl.wpa} for runs vs expected / wickets / win probability added. Filters: chase-defend ${fw.inn2}, first innings ${fw.inn1}, playoffs ${fw.playoff}, must-win ${fw.must_win}, out of form ${fw.bad_form}, rivalry ${fw.rivalry}.`, options: {} },
], { x: 0.7, y: 4.0, w: 8.6, h: 0.85, fontSize: 12, valign: "middle" });
s.addNotes("Step 4 matters most. With few pressure balls, the best estimate of a player's pressure level is their normal level; only a sustained gap moves the score. That is what made the ranking repeatable.");

// ---------------------------------------------------------------- 7. fairness
s = slide("CONTENT", "Method");
s.addText("Six rules keep the comparison fair", { placeholder: "title" });
const mb = N.config.min_balls;
const rules = [
  ["Sample", `At least ${mb.bat.inn2} pressure balls faced or ${mb.bowl.inn2} bowled per core filter; smaller for IPL-only filters`],
  ["Opposition", "Each ball adjusted for who was on the other side"],
  ["Role", "Openers, middle order and finishers ranked within their group; same for powerplay, middle and death bowlers"],
  ["Competition", `IPL and T20I standardised separately; associate-team games weighted ×${N.config.associate_weight}`],
  ["Recency", `Each season back weighs ×${N.config.recency_decay}`],
  ["Rain", "Revised targets and overs used wherever the data has them"],
];
rules.forEach(([h, b], i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.5 + col * 4.6, y = 1.2 + row * 1.22;
  card(s, x, y, 4.4, 1.08, col ? HEX.tintBlue : HEX.tint, `rule-${i}`);
  tb(s, h, { x: x + 0.2, y: y + 0.1, w: 4.0, h: 0.35, fontSize: 15, bold: true, fontFace: THEME.headFontFace, color: col ? HEX.royal : HEX.pink });
  tb(s, b, { x: x + 0.2, y: y + 0.45, w: 4.0, h: 0.58, fontSize: 12, valign: "top" });
});

// ---------------------------------------------------------------- 8. reliability fix
section("Reliability");
s = slide("CONTENT", "Reliability");
s.addText("We rebuilt the scoring until rankings repeated", { placeholder: "title" });
const shortNames = ["Design draft", "+ own-level prior", "+ weighted parts", "+ within role (final)"];
s.addChart(pres.charts.BAR, [
  { name: "Batters", labels: shortNames, values: AB.map((r) => r.bat_rho) },
  { name: "Bowlers", labels: shortNames, values: AB.map((r) => r.bowl_rho) }],
  Object.assign({ x: 0.5, y: 1.15, w: 5.9, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: [HEX.pink, HEX.royal],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", showLegend: true, legendPos: "b", valAxisMinVal: 0,
    valAxisMaxVal: 0.6, valAxisLabelFormatCode: "0.0", valGridLine: { color: "EEE3EA", size: 0.5 }, catGridLine: { style: "none" },
    showTitle: true, title: "Split-half rank correlation (two random halves of matches)", objectName: "ablation-chart" }, chartText));
tb(s, [{ text: `${base.bat_rho.toFixed(2)} → ${fin.bat_rho.toFixed(2)}`, options: { fontSize: 34, bold: true, color: HEX.pink, fontFace: THEME.headFontFace, breakLine: true } },
  { text: "batter repeatability, first draft to final", options: { fontSize: 12, color: HEX.muted } }], { x: 6.7, y: 1.35, w: 2.8, h: 1.2 });
tb(s, [{ text: `${base.bowl_rho.toFixed(2)} → ${fin.bowl_rho.toFixed(2)}`, options: { fontSize: 34, bold: true, color: HEX.royal, fontFace: THEME.headFontFace, breakLine: true } },
  { text: "bowler repeatability", options: { fontSize: 12, color: HEX.muted } }], { x: 6.7, y: 2.7, w: 2.8, h: 1.2 });
tb(s, "Runs above expected repeats far better than wickets or win probability added, so it leads the score.", { x: 6.7, y: 4.0, w: 2.8, h: 0.9, fontSize: 12, valign: "top" });
s.addNotes("Split-half: score players on a random half of matches and on the other half, then correlate. The draft scoring was close to noise for batters. Shrinking toward each player's own level and weighting the repeatable components fixed most of it.");

// ---------------------------------------------------------------- 9. stability
s = slide("CONTENT", "Reliability");
const sm = N.sensitivity_mean_survivors;
s.addText(`On average ${sm.bat} batters and ${sm.bowl} bowlers of 10 hold under other weightings`, { placeholder: "title" });
const wNames = Object.keys(N.sensitivity_by_weights.bat);
s.addChart(pres.charts.BAR, [
  { name: "Batters", labels: wNames, values: wNames.map((k) => N.sensitivity_by_weights.bat[k]) },
  { name: "Bowlers", labels: wNames, values: wNames.map((k) => N.sensitivity_by_weights.bowl[k]) }],
  Object.assign({ x: 0.5, y: 1.15, w: 4.6, h: 3.8, barDir: "bar", barGrouping: "clustered", chartColors: [HEX.pink, HEX.royal],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 10,
    valGridLine: { color: "EEE3EA", size: 0.5 }, catGridLine: { style: "none" }, showTitle: true, title: "Top-10 survivors by weighting (avg of 3 sample cuts)",
    objectName: "sensitivity-chart" }, chartText));
const seasons = Object.keys(N.loso.bat);
s.addChart(pres.charts.BAR, [
  { name: "Batters", labels: seasons, values: seasons.map((k) => N.loso.bat[k]) },
  { name: "Bowlers", labels: seasons, values: seasons.map((k) => N.loso.bowl[k]) }],
  Object.assign({ x: 5.3, y: 1.15, w: 4.2, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: [HEX.pink, HEX.royal],
    showValue: true, dataLabelPosition: "outEnd", showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 10,
    valGridLine: { color: "EEE3EA", size: 0.5 }, catGridLine: { style: "none" }, showTitle: true, title: "Top-10 survivors with one season removed",
    objectName: "loso-chart" }, chartText));

// ---------------------------------------------------------------- 10. dashboard
section("Close");
s = slide("CONTENT", "Close");
s.addText("The dashboard reproduces the lists and re-ranks live", { placeholder: "title" });
const feats = [
  ["Any filters, any weights", "Tick filters, set weights, All-round or Specialist mode, season range and minimum sample"],
  ["Trust beside every rank", "Rank range, P(top 10), choke rate and pressure-ball count in the table"],
  ["Why a player ranks", "Pressure radar, normal-vs-pressure quadrants (Ice, Fire, Choker, Passenger), pressure twins"],
  ["Pressure replay", "Ball-by-ball win probability and pressure through any innings"],
];
feats.forEach(([h, b], i) => {
  const y = 1.2 + i * 0.85;
  s.addShape(pres.shapes.OVAL, { x: 0.5, y: y + 0.08, w: 0.45, h: 0.45, fill: { color: i % 2 ? HEX.royal : HEX.pink }, line: { color: i % 2 ? HEX.royal : HEX.pink }, objectName: `feat-dot-${i}` });
  tb(s, h, { x: 1.15, y, w: 4.6, h: 0.32, fontSize: 15, bold: true, fontFace: THEME.headFontFace });
  tb(s, b, { x: 1.15, y: y + 0.32, w: 4.6, h: 0.45, fontSize: 12, color: HEX.muted, valign: "top" });
});
card(s, 6.1, 1.2, 3.4, 3.3, HEX.tintBlue, "dash-card");
tb(s, "Export = submission", { x: 6.3, y: 1.35, w: 3.0, h: 0.4, fontSize: 15, bold: true, fontFace: THEME.headFontFace, color: HEX.royal });
tb(s, "The submission setup in the dashboard returns exactly the Rank 1–10 lists in this deck and the report: the same engine, the same table.", { x: 6.3, y: 1.8, w: 3.0, h: 1.4, fontSize: 12, valign: "top" });
if (DASH_URL) tb(s, [{ text: DASH_URL, options: { hyperlink: { url: DASH_URL }, color: HEX.pink, bold: true } }], { x: 6.3, y: 3.4, w: 3.0, h: 0.9, fontSize: 11, valign: "top" });

// ---------------------------------------------------------------- 11. limits
s = slide("CONTENT", "Close");
s.addText("What the ranking can and cannot claim", { placeholder: "title" });
const can = ["Who performs above expectation when a ball can swing the match", "How much each rank could move (rank range, P(top 10))", "That results hold across weightings and seasons (previous slide)"];
const lastSeason = Object.keys(N.loso.bat).sort().pop();
const cannot = [`Playoffs are thin: ${N.data.playoff_matches} IPL knockout matches, so they carry a light weight`,
  "Pressure-specific skill beyond a player's normal level is hard to measure; the score leans on output under pressure",
  `Batter list leans on ${lastSeason}: drop it and ${N.loso.bat[lastSeason]} of 10 stay`,
  "No pitch, weather or price data; T20I opposition strength varies"];
[[can, "Can claim", HEX.tint, HEX.pink, 0.5], [cannot, "Cannot claim", HEX.tintBlue, HEX.royal, 5.1]].forEach(([items, h, fill, col, x], k) => {
  card(s, x, 1.2, 4.4, 3.2, fill, `limits-${k}`);
  tb(s, h, { x: x + 0.25, y: 1.35, w: 3.9, h: 0.4, fontSize: 17, bold: true, fontFace: THEME.headFontFace, color: col });
  tb(s, items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1 } })),
    { x: x + 0.25, y: 1.85, w: 3.95, h: 2.45, fontSize: 13, valign: "top", paraSpaceAfter: 8 });
});

// ---------------------------------------------------------------- 12. close
s = slide("DARK", "Close");
s.addText("Pressure, measured and shown with its uncertainty", { placeholder: "title" });
s.addText(`Top 10 batters led by ${L.bat[0].Player}; top 10 bowlers led by ${L.bowl[0].Player}. Every number traces to the supplied ball-by-ball data and one reproducible pipeline.`, { placeholder: "body" });

(async () => {
  await pres.writeFile({ fileName: OUTFILE });
  const skill = process.env.PPTX_SKILL_DIR;
  if (skill) {
    const { applyTheme } = require(path.join(skill, "scripts", "apply_theme.js"));
    await applyTheme(OUTFILE, THEME);
  }
  console.log("wrote", OUTFILE);
})();
