# SupeRR Selector R1

Pressure ratings for IPL and T20I players (2022–2026): who performs above expectation, and above their own usual level, when the next ball can swing the match. Produces the top 10 batters and top 10 bowlers with a bootstrap rank range for each.

- **Submission lists:** `outputs/submission_top10_batters.csv`, `outputs/submission_top10_bowlers.csv`
- **Methodology report:** `reports/SupeRR_Selector_R1_Methodology.pdf` (and `.docx`)
- **Slides:** `reports/SupeRR_Selector_R1.pptx` (and `.pdf`)
- **Dashboard:** https://superr-selector-r1.streamlit.app (or locally: `streamlit run app.py`)

## Reproduce

The supplied competition CSVs are not included. Put them in `data/raw/`, then:

```bash
uv sync
uv run python -m src.build         # data, win probability, leverage, pressure index, aggregates
uv run python -m src.reliability   # bootstrap ranks, split-half, sensitivity, leave-one-season-out
uv run python -m src.report        # locks the lists, report numbers and figures
uv run python -m src.report_extra  # threshold sweep, calibration, worked example, near misses
uv run python -m src.report_doc    # methodology .docx
node reports/build_deck.js         # slides (needs pptxgenjs)
uv run streamlit run app.py
```

Seeds are fixed, so runs are identical. Every tunable setting is in `src/config.py`.

The dashboard needs only the precomputed files in `outputs/` and the packages in `requirements.txt`. That is what Streamlit Community Cloud installs.
