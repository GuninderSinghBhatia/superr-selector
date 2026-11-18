// Builds reports/SupeRR_Selector_R1.pptx from outputs/report_numbers.json (run: node reports/build_deck.js)
// Needs pptxgenjs: set NODE_PATH to a node_modules folder that has it, or `npm install pptxgenjs@3.12.0`.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const N = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "report_numbers.json"), "utf8"));
const X = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "report_extra.json"), "utf8"));
const IMG = path.join(ROOT, "reports", "images");
const CREDITS = JSON.parse(fs.readFileSync(path.join(IMG, "credits.json"), "utf8"));
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

pres.defineSlideMaster({ title: "DIVIDER", background: { color: HEX.royal },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.6, w: 4.6, h: 1.5, fontSize: 34, bold: true,
      color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.25, w: 4.6, h: 1.4, fontSize: 16,
      color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ] });

// Photos: Wikimedia Commons, credited on the slide and on the credits slide.
function photo(s, key, x, y, w, h, name) {
  const c = CREDITS[key];
  const r = c.w / c.h, box = w / h;
  const iw = r > box ? h * r : w, ih = r > box ? h : w / r;   // image size that covers the box
  s.addImage({ path: path.join(IMG, key), x, y, w: iw, h: ih, sizing: { type: "cover", w, h }, objectName: name,
    altText: `Photo: ${c.title.replace(/\.jpe?g$/i, "")}` });
}
function credit(s, key, x, y, w, color) {
  const c = CREDITS[key];
  const who = c.license === "CC0" ? "public domain (CC0)" : `${c.artist}, ${c.license}`;
  s.addText(`Photo: ${who}, Wikimedia Commons`, { isTextBox: true, x, y, w, h: 0.22, fontSize: 7, color: color || HEX.white,
    fontFace: THEME.bodyFontFace, margin: 0, align: "right" });
}
function divider(sec, title, body, key) {
  const sl = pres.addSlide({ masterName: "DIVIDER", sectionTitle: sec });
  photo(sl, key, 5.6, 0, 4.4, 5.625, `divider-photo-${key}`);
  sl.addText(title, { placeholder: "title" });
  sl.addText(body, { placeholder: "body" });
  credit(sl, key, 5.7, 5.33, 4.2);
  return sl;
}

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
photo(s, "hero_final.jpg", 0, 0, 10, 5.625, "title-photo");
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 5.625, fill: { color: HEX.ink, transparency: 35 },
  line: { color: HEX.ink, transparency: 100 }, objectName: "title-overlay" });
s.addText("Who rises when the match is on the line", { placeholder: "title" });
credit(s, "hero_final.jpg", 5.5, 5.33, 4.3);
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

// ---------------------------------------------------------------- near misses
{
  const NM = X.near_misses;
  const sl = slide("CONTENT", "Answer");
  sl.addText("Ranks 8 to 15 are close to interchangeable", { placeholder: "title" });
  [["bat", "Batters ranked 11–15", 0.5], ["bowl", "Bowlers ranked 11–15", 5.1]].forEach(([role, head, x]) => {
    tb(sl, head, { x, y: 1.15, w: 4.4, h: 0.35, fontSize: 15, bold: true, fontFace: THEME.headFontFace, color: role === "bat" ? HEX.pink : HEX.royal });
    const hdr = ["#", "Player", "Rank range", "P(top 10)"].map((h) => ({ text: h, options: { bold: true, color: HEX.white, fill: { color: HEX.royal }, fontSize: 11 } }));
    const rows = [hdr].concat(NM[role].map((r, i) => {
      const o = { fontSize: 11, color: HEX.ink, fill: { color: i % 2 ? HEX.white : HEX.tint } };
      return [{ text: String(r.rank), options: Object.assign({}, o, { bold: true, color: HEX.pink }) },
        { text: r.player, options: Object.assign({}, o, { bold: true }) }, { text: r.range, options: o },
        { text: `${Math.round(r.p_top10 * 100)}%`, options: o }];
    }));
    sl.addTable(rows, { x, y: 1.55, w: 4.4, colW: [0.4, 2.0, 1.0, 1.0], rowH: 0.3, fontFace: THEME.bodyFontFace,
      border: { type: "none" }, valign: "middle", margin: [0, 0.06, 0, 0.06], objectName: `${role}-near-misses` });
  });
  const best = NM.bat.reduce((a, b) => (b.p_top10 > a.p_top10 ? b : a));
  const low = L.bat.slice(7).reduce((a, b) => (b["P(top 10)"] < a["P(top 10)"] ? b : a));
  card(sl, 0.5, 3.6, 9.0, 1.2, HEX.tintBlue, "near-miss-note");
  tb(sl, [{ text: `${best.player} (#${best.rank}) makes the top 10 in ${Math.round(best.p_top10 * 100)}% of resamples, `, options: { bold: true } },
    { text: `against ${Math.round(low["P(top 10)"] * 100)}% for ${low.Player} at #${low.Rank}. We submit the most likely top 10 and show the boundary honestly rather than claim exact positions.`, options: {} }],
  { x: 0.75, y: 3.7, w: 8.5, h: 1.0, fontSize: 13, valign: "middle" });
  sl.addNotes("The boundary of the top 10 is where the uncertainty matters most. These players are one good season from the list.");
}

// ---------------------------------------------------------------- 4. what pressure is
section("Method");
divider("Method", "How we measure pressure", "Ball by ball, from how far the next delivery can swing the match.", "ahmedabad.jpg");
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

// ---------------------------------------------------------------- pressure map
s = slide("CONTENT", "Method");
s.addText("Pressure peaks when wickets fall in clusters", { placeholder: "title" });
s.addImage({ path: path.join(ROOT, "reports", "figures", "pressure_map.png"), x: 1.8, y: 1.05, w: 6.4, h: 6.4 * 554 / 1140,
  objectName: "pressure-map", altText: "Heat map of average pressure index by over and wickets down, innings 1 and 2" });
tb(s, "Average pressure index by over (x) and wickets down (y). A side cruising with wickets in hand sees little pressure; four to seven down in the middle and late overs is where it concentrates. No native chart type draws a heat map, so this one is an image.",
  { x: 0.9, y: 4.3, w: 8.2, h: 0.7, fontSize: 11, color: HEX.muted, valign: "top" });

// ---------------------------------------------------------------- worked example
{
  const E = X.worked_example, S = E.series;
  const sl = slide("CONTENT", "Method");
  sl.addText(`One chase, ball by ball: ${E.season} ${E.stage}`, { placeholder: "title" });
  const labels = S.wp.map((_, i) => String(i + 1));
  sl.addChart([
    { type: pres.charts.AREA, data: [{ name: "Pressure index (percentile)", labels, values: S.pi }],
      options: { chartColors: [HEX.pink], chartColorsOpacity: 30 } },
    { type: pres.charts.LINE, data: [{ name: "Chasing side win probability", labels, values: S.wp }],
      options: { chartColors: [HEX.royal], lineSize: 2, lineDataSymbol: "none" } },
  ], Object.assign({ x: 0.5, y: 1.1, w: 6.3, h: 3.9, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%",
    catAxisLabelFrequency: 20, catAxisTitle: "Ball of the chase", showCatAxisTitle: true, catAxisTitleFontSize: 10,
    catAxisTitleColor: HEX.ink, showLegend: true, legendPos: "b", valGridLine: { color: "EEE3EA", size: 0.5 },
    catGridLine: { style: "none" }, objectName: "worked-example-chart" }, chartText));
  card(sl, 7.0, 1.2, 2.5, 3.7, HEX.tint, "worked-example-card");
  tb(sl, E.teams, { x: 7.2, y: 1.35, w: 2.15, h: 0.6, fontSize: 13, bold: true, fontFace: THEME.headFontFace, color: HEX.royal, valign: "top" });
  tb(sl, [{ text: `${E.pressure_balls} of ${E.balls}`, options: { fontSize: 26, bold: true, color: HEX.pink, fontFace: THEME.headFontFace, breakLine: true } },
    { text: "balls were pressure balls", options: { fontSize: 11, color: HEX.muted } }], { x: 7.2, y: 2.0, w: 2.15, h: 0.9 });
  tb(sl, [{ text: `Target ${E.target}`, options: { bold: true, breakLine: true } },
    { text: `Win probability starts at ${Math.round(E.start_wp * 100)}%, then swings with each of the ${S.wickets.length} wickets. ${E.result.replace(" Won ", " won ")}.`, options: {} }],
  { x: 7.2, y: 3.0, w: 2.15, h: 1.8, fontSize: 11, valign: "top" });
  sl.addNotes("This is the IPL knock-out chase with the highest average leverage. Every ball here counts towards the chasing/defending and playoff filters of the players involved, weighted by its leverage.");
}

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

// ---------------------------------------------------------------- threshold choice
{
  const T = X.threshold_sweep;
  const chosen = Math.round((1 - N.config.pressure_pct) * 100);
  const sl = slide("CONTENT", "Method");
  sl.addText(`Why the top ${chosen}% of balls count as pressure`, { placeholder: "title" });
  const labs = T.map((r) => `Top ${Math.round(r.pressure_share * 100)}%`);
  sl.addChart(pres.charts.BAR, [
    { name: "Batters", labels: labs, values: T.map((r) => r.bat_rho) },
    { name: "Bowlers", labels: labs, values: T.map((r) => r.bowl_rho) }],
  Object.assign({ x: 0.5, y: 1.15, w: 5.9, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: [HEX.pink, HEX.royal],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", showLegend: true, legendPos: "b", valAxisMinVal: 0,
    valAxisMaxVal: 0.6, valAxisLabelFormatCode: "0.0", valGridLine: { color: "EEE3EA", size: 0.5 }, catGridLine: { style: "none" },
    showTitle: true, title: "Split-half repeatability at each threshold", objectName: "threshold-chart" }, chartText));
  const t30 = T.find((r) => Math.round(r.pressure_share * 100) === chosen), t20 = T.find((r) => Math.round(r.pressure_share * 100) === 20);
  card(sl, 6.7, 1.25, 2.8, 3.6, HEX.tintBlue, "threshold-note");
  tb(sl, "The trade-off", { x: 6.9, y: 1.4, w: 2.4, h: 0.4, fontSize: 15, bold: true, fontFace: THEME.headFontFace, color: HEX.royal });
  tb(sl, [
    { text: `Narrower cuts isolate tenser balls but leave fewer players with enough of them.`, options: { bullet: { indent: 14 }, breakLine: true } },
    { text: `At 20%, bowlers repeat a little better (${t20.bowl_rho.toFixed(2)}) but batters drop to ${t20.bat_rho.toFixed(2)} and a third fewer qualify.`, options: { bullet: { indent: 14 }, breakLine: true } },
    { text: `At 40%, four balls in ten would count: no longer pressure.`, options: { bullet: { indent: 14 } } },
  ], { x: 6.9, y: 1.85, w: 2.45, h: 2.9, fontSize: 12, valign: "top", paraSpaceAfter: 6 });
}

divider("Method", "How we score performance", "Against what each situation usually yields, then against the player's own usual level.", "ball.jpg");

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
divider("Reliability", "How far to trust it", "Every check re-runs the same scoring engine on perturbed data.", "floodlight.jpg");
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
photo(s, "wankhede.jpg", 6.1, 1.2, 3.4, 1.45, "dash-photo");
credit(s, "wankhede.jpg", 6.1, 2.68, 3.4, HEX.muted);
card(s, 6.1, 2.95, 3.4, 1.95, HEX.tintBlue, "dash-card");
tb(s, "Export = submission", { x: 6.3, y: 3.05, w: 3.0, h: 0.35, fontSize: 15, bold: true, fontFace: THEME.headFontFace, color: HEX.royal });
tb(s, "Its submission setup returns exactly the lists in this deck and the report.", { x: 6.3, y: 3.42, w: 3.0, h: 0.75, fontSize: 12, valign: "top" });
if (DASH_URL) tb(s, [{ text: DASH_URL.replace("https://", ""), options: { hyperlink: { url: DASH_URL }, color: HEX.pink, bold: true } }], { x: 6.3, y: 4.25, w: 3.0, h: 0.4, fontSize: 11, valign: "top" });

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
photo(s, "chinnaswamy.jpg", 0, 0, 10, 5.625, "close-photo");
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 5.625, fill: { color: HEX.royal, transparency: 25 },
  line: { color: HEX.royal, transparency: 100 }, objectName: "close-overlay" });
s.addText("Pressure, measured and shown with its uncertainty", { placeholder: "title" });
s.addText(`Top 10 batters led by ${L.bat[0].Player}; top 10 bowlers led by ${L.bowl[0].Player}. Every number traces to the supplied ball-by-ball data and one reproducible pipeline.`, { placeholder: "body" });
credit(s, "chinnaswamy.jpg", 5.5, 5.33, 4.3);

// ---------------------------------------------------------------- image credits
s = slide("CONTENT", "Close");
s.addText("Image credits", { placeholder: "title" });
tb(s, Object.entries(CREDITS).map(([k, c], i, a) => ({
  text: `${c.title.replace(/\.jpe?g$/i, "")} — ${c.license === "CC0" ? "public domain (CC0)" : `${c.artist}, ${c.license}`}. ${c.page}`,
  options: { bullet: { indent: 14 }, breakLine: i < a.length - 1 } })),
{ x: 0.5, y: 1.2, w: 9.0, h: 3.6, fontSize: 11, valign: "top", paraSpaceAfter: 6 });
tb(s, "All photos from Wikimedia Commons under the licences shown, cropped to fit. Charts and data are our own, from the supplied files.",
  { x: 0.5, y: 4.7, w: 9.0, h: 0.4, fontSize: 10, color: HEX.muted });

(async () => {
  await pres.writeFile({ fileName: OUTFILE });
  const skill = process.env.PPTX_SKILL_DIR;
  if (skill) {
    const { applyTheme } = require(path.join(skill, "scripts", "apply_theme.js"));
    await applyTheme(OUTFILE, THEME);
  }
  console.log("wrote", OUTFILE);
})();
