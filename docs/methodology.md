# State-Aware Screening Methodology

This project uses statistical screening to prioritize records for contextual review. A flag is not evidence that a jurisdiction reported an error or that improper activity occurred.

## Why comparisons are made within states

State laws and procedures shape mail-ballot eligibility, verification, curing, deadlines, and list maintenance. EAVS reporting structures also differ across states. The initial screen therefore compares eligible jurisdictions only with other eligible jurisdictions in the same state or territory.

A state model requires at least 10 eligible jurisdiction peers. Records from smaller peer groups remain in the processed data but are not assigned a state-aware priority flag.

## Mail-ballot rejection screen

For jurisdiction $i$ in state $s$, the observed rejected-ballot count is modeled as:

$$
X_{is} \sim \operatorname{BetaBinomial}(n_{is}, \alpha_s, \beta_s)
$$

where $n_{is}$ is the number of mail ballots returned. Separate state parameters are estimated by maximum likelihood. The beta-binomial distribution is used instead of a simple binomial distribution because it allows the underlying rejection probability to vary across jurisdictions.

The screen then:

1. Calculates the upper-tail probability of observing at least the reported number of rejected ballots.
2. Applies a within-state Bonferroni threshold of $0.05 / m_s$, where $m_s$ is the number of eligible state peers.
3. Requires the jurisdiction's 95% Wilson interval lower bound to exceed the state's weighted rejection rate.

The state model is an in-sample screening model: each candidate contributes to the state distribution used to assess it. This tends to broaden the fitted distribution when an extreme value is present, but it does not eliminate model-dependence. Flags remain leads for contextual review.

## List-maintenance screen

List-maintenance intensity is defined as total removals divided by registered voters, multiplied by 1,000. Because the numerator covers activity over the reporting period while the denominator is a point-in-time count, this is not a probability.

Within each state, the screen applies the modified z-score to `log1p(removals per 1,000)`:

$$
M_i = \frac{0.6745(x_i - \widetilde{x})}{\operatorname{MAD}}
$$

High-side values above 3.5 are prioritized for review. The log transform reduces the influence of a long right tail, while the median and median absolute deviation are more resistant to extreme observations than the mean and standard deviation.

## Important limitations

- EAVS is a biennial administrative survey, not a longitudinal voter-file monitoring system.
- Jurisdiction types and reporting practices vary even within states.
- Statistical extremeness cannot identify the cause of a reported value.
- State policy variables are not yet included directly in the model.
- Multiple high values in one state may reflect a shared administrative or reporting pattern.
- Contextual validation against state and local documentation is required before any substantive claim.

## Contextual-review protocol

Mail-ballot candidates selected by the statistical screen are reviewed in four stages:

1. Recheck `counted + rejected = returned` for the jurisdiction aggregate.
2. Sum all nonnegative detailed rejection-reason fields and compare that sum with the reported rejection total.
3. Review EAVS comments and cure fields without converting valid skips or unavailable responses to zero.
4. Search official state and local sources for a directly comparable count or rate and, separately, for policy or reporting context.

Each record then receives one evidence label:

- **Externally corroborated:** an official source independently reports a closely matching jurisdiction-level rate or count.
- **Internally reconciled:** detailed EAVS reasons account for the total and official policy context is consistent, but no independent jurisdiction-level count was located.
- **Partially reconciled:** detailed EAVS reasons account for part of the total, with a documented reporting limitation.
- **Unresolved:** the aggregate arithmetic is valid, but the reviewed public record does not explain the reason distribution or independently confirm the mail-ballot rate.

These labels describe evidence strength. They are not findings of error, fraud, misconduct, or disenfranchisement.

## Method references

- [U.S. Election Assistance Commission, 2024 EAVS Comprehensive Report](https://www.eac.gov/sites/default/files/2025-07/2024_EAVS_Report_508.pdf)
- [U.S. Election Assistance Commission, EAVS reports and Version 2.0 data](https://www.eac.gov/research-and-data/studies-and-reports)
- [NIST/SEMATECH e-Handbook: Detection of Outliers](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm)
