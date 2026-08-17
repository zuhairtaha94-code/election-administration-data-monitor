# Election Administration Data Monitor

A reproducible Python analysis of public U.S. election-administration data, with an emphasis on data quality, responsible outlier triage, and clear communication for nontechnical stakeholders.

## Research question

**Which local election jurisdictions reported unusual 2024 voter-registration list-maintenance or mail-ballot rejection rates after accounting for jurisdiction size, data completeness, and state context?**

This project uses the U.S. Election Assistance Commission's 2024 Election Administration and Voting Survey (EAVS). The EAVS contains state- and local-level information about voter registration, list maintenance, voting methods, mail ballots, and election administration.

Official source: [U.S. Election Assistance Commission — EAVS reports and datasets](https://www.eac.gov/research-and-data/studies-and-reports)

## Why this question matters

Election administrators work with large, decentralized datasets collected under different state laws, administrative systems, and reporting practices. A rate that appears unusual may reflect a genuine operational issue, a policy difference, a reporting convention, missing data, or a small denominator.

This project therefore treats an outlier as a **prompt for contextual review**, not as evidence of error, fraud, misconduct, or disenfranchisement.

## Planned analytical workflow

1. Audit the dataset and codebook before selecting variables.
2. Standardize missing-value codes, data types, and jurisdiction identifiers.
3. Validate denominators and flag incomplete or internally inconsistent records.
4. Construct interpretable registration and mail-ballot metrics.
5. Identify unusual reported values using robust, transparent methods.
6. Compare jurisdictions only within defensible peer groups.
7. Add policy and reporting context before drawing conclusions.
8. Communicate findings, limitations, and open questions in accessible visuals and prose.

## Responsible interpretation rules

- Reported outliers are not allegations.
- Missing and suppressed values will not be treated as zero.
- Rates with very small denominators will be excluded or clearly qualified.
- State policy and reporting differences will be considered before comparison.
- The analysis will not use personally identifiable voter information.
- Methods, exclusions, and unresolved data-quality questions will be documented.

## Implemented validation rules

- Mail-ballot rejection rates use `C9a / C1b * 100`, following the EAC's published definition.
- Jurisdictions with 100–499 returned mail ballots remain available for descriptive review, but formal comparisons require at least 500 returns.
- A mail-ballot reconciliation gap is treated as material only when `C8a + C9a - C1b` differs by more than 10 ballots **and** more than 1% of returned ballots.
- Eligible mail rates include 95% Wilson confidence intervals so uncertainty remains visible.
- List-maintenance intensity uses `A12a / A1a * 1,000` and requires at least 1,000 registered voters for comparison.
- The list-maintenance measure compares two-year removal activity with a point-in-time registration count. It is not a probability and can exceed 1,000 removals per 1,000 registered voters.

## Repository structure

```text
election-administration-data-monitor/
├── data/
│   ├── raw/          # Original source files; not committed to GitHub
│   ├── processed/    # Reproducible derived files; generally not committed
│   ├── source_manifest.json
│   └── README.md
├── docs/
│   └── decision_log.md
├── notebooks/        # Numbered exploratory and analytical notebooks
├── reports/
│   └── figures/      # Final publication-ready figures
├── scripts/          # Reproducible data acquisition and audit commands
├── src/              # Reusable cleaning, validation, and analysis functions
├── tests/            # Automated checks for critical transformations
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Project status

**Phase 3 — Metric validation complete.** The official source release is checksum-verified. The data contain 6,461 jurisdiction records and 535 documented columns, with one unique FIPS identifier per record and complete alignment between the CSV and codebook. After denominator and reconciliation rules, 2,621 jurisdictions across 50 states and territories are eligible for mail-rejection comparison, and 4,640 jurisdictions across 53 states and territories are eligible for list-maintenance comparison. State-aware outlier triage is next.

## Reproducibility

The raw EAVS files are not stored in this repository. Download instructions, source URLs, release versions, integrity checks, and build commands are documented in `data/README.md`.

Run the current pipeline from the repository root:

```bash
python scripts/download_eavs.py
python scripts/audit_source_data.py
python scripts/build_analysis_dataset.py
python -m unittest discover -s tests -v
```

## License

Code in this repository is available under the MIT License. Source datasets remain subject to the terms and documentation of their original publishers.
