# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: the judges of the SupeRR Selector Round 1 competition on Unstop. They review a submission made of two ranked lists (top 10 batters, top 10 bowlers), a methodology report, and a presentation. They need to see quickly why each name is on the list and how far to trust it.

Secondary: the submitting team, who use the same dashboard to explore and tune the ranking before locking the lists. Judges are the audience the design is for; the team's needs follow from it.

## Product Purpose

Rate every IPL and T20I player on how they perform under pressure relative to their own usual level, then submit the top 10 batters and top 10 bowlers with a reproducible methodology. The dashboard lets a viewer pick any set of pressure filters, weight them, and get a ranked list that matches the submitted Rank 1–10 lists exactly. Success is a ranking the judges find credible, with its uncertainty shown beside it.

## Positioning

Pressure is scored per ball from win-probability leverage and measured as performance above expectation for the player's own context, not raw runs or wickets. Every rank carries its own reliability evidence (bootstrap rank range, split-half consistency, sensitivity to weights, leave-one-season-out). A ranking that shows how fragile it is, rather than only a score, is the position a reputation-based list cannot copy.

## Operating Context

Presented live on a laptop (run locally with Streamlit), alongside a written methodology report and a slide presentation. Data comes only from the supplied files: ball-by-ball (about 201k deliveries), matches, playing eleven, competitions, teams and player mapping, covering 883 matches from 2022 to 2026, 371 of them IPL. Heavy computation runs offline in Python; the dashboard reads precomputed tables so every filter change responds instantly.

## Capabilities and Constraints

- Six pressure filters: chasing/defending, first innings, must-win, playoff, rivalry, out of form. The last four are IPL only.
- All-round (weighted average) and Specialist (best selected filter) modes; season range and minimum-sample controls.
- Views: ranked top 10 with rank ranges and choke rate, pressure profile radar, normal-vs-pressure scatter (Ice, Fire, Choker, Passenger), pressure twins, pressure replay through an innings, a method and reliability tab, CSV export of Rank 1–10.
- Rank ranges are valid only for the submission setup they were bootstrapped on; the interface says so.
- Choke rate is displayed but not part of the score (it had near-zero reliability).
- Terminology to keep consistent: pressure ball, pressure index, leverage, choke rate, rank range, submission setup.
- Stack: Python, pandas, scikit-learn, Streamlit, Plotly. Single-page Streamlit app.

## Brand Commitments

The dashboard uses the Rajasthan Royals colour scheme (royal blue and pink), requested by the user. Product name is SupeRR Selector. No other brand assets or voice rules have been given.

## Evidence on Hand

Real data in `data/raw/`. Built outputs in `outputs/` (scores, aggregates, validation table, rivalry pairs, reliability tables). No player prices, pitch reports, weather, or points table exist in the data; the points table and rivalry flags are derived from the match results. No testimonials, benchmarks, or external claims are available and none should be invented.

## Product Principles

1. Show uncertainty beside every rank; never present a score as more certain than the data supports.
2. Every number on screen traces to the supplied data and the same table the report uses.
3. The ranked list is the first thing a judge sees; supporting views serve it.
4. Explain only what a judge needs to trust a name: why it ranks, how stable it is, what it rests on.
5. The live demo must be robust and instant; no view depends on a slow or fragile step.
