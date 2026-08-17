# Reports

This directory contains reproducible audit and validation summaries, the final analytical brief, and supporting figures. Draft exploratory output is not treated as a final finding.

- `data_audit_summary.json` documents source shape, codebook alignment, sentinel values, and initial metric checks.
- `metric_validation_summary.json` documents denominator sensitivity, quality gates, comparison coverage, and eligible metric distributions.
- `outlier_triage_summary.json` documents state-model coverage, screening rules, review-candidate counts, and the records selected by the mail screen.
- `context_review.csv` is the candidate-level evidence table, including reconciliation checks, dominant reported reasons, cure counts, official-source links, and evidence status.
- `context_review_summary.json` provides the compact machine-readable outcome of the contextual review.
- `analytical_brief.md` is the complete written portfolio brief; the rendered PDF is in `output/pdf/`.
- `figures/` contains reproducibly generated PNG and SVG figures for the project README and final brief.
