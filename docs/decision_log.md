# Analytical Decision Log

This file records consequential project decisions and the reasoning behind them. It is intended to make the analysis easier to audit and explain.

## 2026-08-17 — Select the 2024 EAVS as the primary source

**Decision:** Begin with Version 2.0 of the U.S. Election Assistance Commission's 2024 Election Administration and Voting Survey.

**Rationale:** The EAVS is an authoritative, public, nationwide source with state- and local-level election-administration data. It includes topics directly related to the project's target role, including voter registration, list maintenance, and mail voting. Its codebook and documented corrections make it suitable for a reproducible portfolio project.

**Limitation:** The EAVS is a periodic administrative survey. It is not a sequence of individual-level voter-file snapshots and therefore cannot reproduce VoteShield's exact monitoring workflow.

## 2026-08-17 — Use “outlier” or “unusual reported value,” not “anomaly” as a conclusion

**Decision:** Treat statistical flags as questions for further review.

**Rationale:** A value may be unusual because of reporting conventions, state law, missingness, small denominators, or legitimate administrative differences. Statistical extremeness alone does not establish an error or improper activity.

## 2026-08-17 — Do not commit raw data

**Decision:** Store source data locally and document official download locations and release versions.

**Rationale:** This keeps the repository lightweight, preserves a clear distinction between source and code, and requires the analysis to be reproducible from the publisher's files.

## 2026-08-17 — Separate notebooks from reusable code

**Decision:** Use notebooks for exploration and explanation, and move repeatable cleaning, validation, and calculation logic into `src/`.

**Rationale:** Notebooks are useful narratives, but reusable functions are easier to test, audit, and maintain.

## 2026-08-17 — Preserve EAVS response categories before analysis

**Decision:** Interpret `-77` as a valid skip, `-88` as responded/does not apply, `-99` as responded/data not available, and blank or nonnumeric cells as missing. Convert all four categories to null only when constructing a numeric metric, while retaining separate counts for data-quality reporting.

**Rationale:** These categories have different administrative meanings. Treating the negative values as numbers would corrupt totals and averages; collapsing the categories too early would hide important reporting patterns.

## 2026-08-17 — Define the initial mail-ballot rejection rate as C9a/C1b

**Decision:** Use total mail ballots rejected divided by total mail ballots returned by voters, multiplied by 100.

**Rationale:** This follows the definition used in the EAC's 2024 comprehensive report. The analysis will require a positive denominator and will later add a minimum-denominator threshold.

**Quality-control note:** For records where all three values are available, compare `C8a + C9a` with `C1b`. A nonzero difference is a reporting or reconciliation flag requiring context, not proof that any individual field is wrong.

## 2026-08-17 — Use tiered mail-ballot denominator rules

**Decision:** Retain jurisdictions with 100–499 returned mail ballots for descriptive review, but require at least 500 returned ballots for formal comparison.

**Rationale:** A single rejected ballot changes the observed rate by one percentage point when the denominator is 100, but by no more than 0.2 percentage points at 500. The 500-ballot comparison threshold retains 2,676 jurisdictions across 50 states and territories before reconciliation exclusions. Wilson confidence intervals are also retained so the threshold does not imply equal precision above the cutoff.

**Tradeoff:** A threshold improves rate stability but disproportionately excludes small jurisdictions. Descriptive records remain available, and the final report will disclose the resulting coverage rather than generalize to all jurisdictions.

## 2026-08-17 — Define a material mail-ballot reconciliation gap

**Decision:** Flag a reconciliation difference as material only when its absolute value exceeds both 10 ballots and 1% of returned mail ballots.

**Rationale:** Requiring both conditions avoids treating a few ballots in a small jurisdiction or a tiny proportional difference in a large jurisdiction as equivalent to a consequential mismatch. At the 500-ballot comparison threshold, this rule excludes 55 of 2,676 otherwise eligible records.

**Limitation:** This is a transparent triage rule, not proof that excluded records are erroneous. The thresholds will remain visible as named constants and in the validation summary.

## 2026-08-17 — Treat list removals as administrative intensity, not probability

**Decision:** Report `A12a / A1a * 1,000` only as removals per 1,000 registered voters and require at least 1,000 registered voters for formal comparison.

**Rationale:** The numerator covers removal activity over the EAVS reporting period, while the denominator is a point-in-time registration count. Turnover means the measure may legitimately exceed 1,000; it must not be described as a share of voters removed. The threshold limits small-denominator instability while retaining 4,640 jurisdictions across 53 states and territories.

## 2026-08-17 — Compare jurisdictions within states

**Decision:** Build state-aware screens only where at least 10 eligible jurisdiction peers are available.

**Rationale:** State laws and procedures shape mail-ballot verification, curing, deadlines, and list maintenance. State reporting structures also differ. Within-state screening reduces—but does not eliminate—these comparability problems. Ten peers provide a minimum basis for fitting or estimating a state distribution without implying that every state model is equally informative.

## 2026-08-17 — Use a beta-binomial screen for mail rejections

**Decision:** Fit a separate beta-binomial distribution to eligible jurisdiction counts within each state. Flag a high-side record when its upper-tail probability is below a within-state Bonferroni threshold of `0.05 / peer count` and its 95% Wilson interval lower bound exceeds the state weighted rejection rate.

**Rationale:** A beta-binomial model uses both rejected and returned ballot counts while allowing genuine rejection probabilities to vary across jurisdictions. This is more appropriate than treating every ballot as an independent draw from one fixed state probability. The familywise correction limits the chance of producing review candidates merely because many jurisdictions were screened.

**Limitation:** The model is a screening device, not a causal or error-detection model. Each record contributes to the in-sample state distribution, and policy or reporting differences may remain within states.

## 2026-08-17 — Use a robust screen for list-maintenance intensity

**Decision:** Apply the modified z-score to `log1p(removals per 1,000)` within eligible state peer groups and prioritize high-side values above 3.5.

**Rationale:** List-maintenance intensity is continuous, nonnegative, and strongly right-skewed. The log transform reduces skew, while the median and median absolute deviation reduce sensitivity to extreme observations. The 3.5 threshold follows the potential-outlier guidance summarized in the NIST/SEMATECH e-Handbook.

**Limitation:** The score describes statistical extremeness only. It does not account directly for the timing or legal basis of removals and must not be interpreted as the share of current voters removed.
