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
