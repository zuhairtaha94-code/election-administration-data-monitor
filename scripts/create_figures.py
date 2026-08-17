"""Create publication-ready figures from the state-aware triage output."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRIAGE_PATH = PROJECT_ROOT / "data" / "processed" / "outlier_triage.csv"
FIGURE_DIR = PROJECT_ROOT / "reports" / "figures"

NAVY = "#173F5F"
BLUE = "#2D6A8A"
ORANGE = "#D07A32"
LIGHT_BLUE = "#B8CAD7"
GRAY = "#5B6573"


def label(frame: pd.DataFrame) -> pd.Series:
    return frame["Jurisdiction_Name"].str.title() + ", " + frame["State_Abbr"]


def save_figure(figure: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_DIR / f"{stem}.png", dpi=220, bbox_inches="tight")
    svg_path = FIGURE_DIR / f"{stem}.svg"
    figure.savefig(svg_path, bbox_inches="tight")
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(figure)


def plot_mail_candidates(triage: pd.DataFrame) -> None:
    candidates = triage.loc[triage["mail_high_priority_review"]].copy()
    candidates = candidates.sort_values("mail_rejection_rate_pct")
    candidates["label"] = label(candidates)
    positions = range(len(candidates))

    figure, axis = plt.subplots(figsize=(11, 6.6))
    axis.hlines(
        positions,
        candidates["mail_state_weighted_rate_pct"],
        candidates["mail_rejection_rate_pct"],
        color=LIGHT_BLUE,
        linewidth=4,
        zorder=1,
    )
    axis.scatter(
        candidates["mail_state_weighted_rate_pct"],
        positions,
        marker="D",
        s=48,
        color=ORANGE,
        label="State weighted rate",
        zorder=3,
    )
    axis.scatter(
        candidates["mail_rejection_rate_pct"],
        positions,
        s=76,
        color=NAVY,
        label="Jurisdiction rate",
        zorder=3,
    )
    for position, rate in zip(positions, candidates["mail_rejection_rate_pct"]):
        axis.annotate(
            f"{rate:.1f}%",
            (rate, position),
            xytext=(7, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color=NAVY,
        )

    axis.set_yticks(list(positions), candidates["label"])
    axis.set_xlabel("Returned mail ballots rejected (%)")
    axis.set_ylabel("")
    axis.grid(axis="x", color="#E6E9ED", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    axis.legend(frameon=False, loc="lower right")
    figure.suptitle(
        "Mail-ballot rates selected for contextual review",
        x=0.08,
        y=0.98,
        ha="left",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    axis.set_title(
        "State-aware beta-binomial screen; 2024 EAVS Version 2.0",
        loc="left",
        fontsize=11,
        color=GRAY,
        pad=14,
    )
    figure.text(
        0.08,
        0.01,
        "Flags are statistical review candidates—not evidence of error, fraud, misconduct, or disenfranchisement.",
        fontsize=9,
        color=GRAY,
    )
    figure.subplots_adjust(left=0.27, bottom=0.12, top=0.84)
    save_figure(figure, "mail_review_candidates")


def plot_removal_candidates(triage: pd.DataFrame) -> None:
    candidates = (
        triage.loc[triage["removal_high_priority_review"]]
        .nlargest(12, "removal_modified_z")
        .sort_values("removal_modified_z")
        .copy()
    )
    candidates["label"] = label(candidates)
    positions = range(len(candidates))

    figure, axis = plt.subplots(figsize=(11, 7.4))
    axis.barh(
        list(positions),
        candidates["removal_modified_z"],
        color=BLUE,
        height=0.66,
    )
    axis.axvline(
        3.5,
        color=ORANGE,
        linewidth=2,
        linestyle="--",
        label="Review threshold (3.5)",
    )
    for position, score, rate in zip(
        positions,
        candidates["removal_modified_z"],
        candidates["removals_per_1000_registered"],
    ):
        axis.annotate(
            f"{score:.1f}  |  {rate:.0f} per 1,000",
            (score, position),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=8.5,
            color=NAVY,
        )

    axis.set_yticks(list(positions), candidates["label"])
    axis.set_xlabel("Within-state modified z-score (log-transformed intensity)")
    axis.set_ylabel("")
    axis.grid(axis="x", color="#E6E9ED", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)
    axis.legend(frameon=False, loc="lower right")
    figure.suptitle(
        "Highest-priority list-maintenance review candidates",
        x=0.08,
        y=0.98,
        ha="left",
        fontsize=17,
        fontweight="bold",
        color=NAVY,
    )
    axis.set_title(
        "Top 12 robust within-state scores; 2024 EAVS Version 2.0",
        loc="left",
        fontsize=11,
        color=GRAY,
        pad=14,
    )
    figure.text(
        0.08,
        0.01,
        "Removal intensity is a two-year activity measure, not the share of current voters removed. Flags require context.",
        fontsize=9,
        color=GRAY,
    )
    figure.subplots_adjust(left=0.37, right=0.88, bottom=0.12, top=0.86)
    save_figure(figure, "removal_review_candidates")


def main() -> None:
    triage = pd.read_csv(TRIAGE_PATH, dtype={"FIPSCode": "string"})
    plot_mail_candidates(triage)
    plot_removal_candidates(triage)
    print("Wrote reports/figures/mail_review_candidates.(png|svg)")
    print("Wrote reports/figures/removal_review_candidates.(png|svg)")


if __name__ == "__main__":
    main()
