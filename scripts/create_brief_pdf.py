"""Create the publication-ready contextual-review brief as a PDF."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = PROJECT_ROOT / "reports" / "context_review.csv"
TRIAGE_SUMMARY_PATH = PROJECT_ROOT / "reports" / "outlier_triage_summary.json"
FIGURE_PATH = PROJECT_ROOT / "reports" / "figures" / "mail_review_candidates.png"
OUTPUT_PATH = PROJECT_ROOT / "output" / "pdf" / "election_administration_data_brief.pdf"

NAVY = colors.HexColor("#12304A")
BLUE = colors.HexColor("#2D6A8A")
TEAL = colors.HexColor("#2A8C82")
GOLD = colors.HexColor("#E0A33A")
CORAL = colors.HexColor("#C95D4B")
INK = colors.HexColor("#22313F")
MUTED = colors.HexColor("#5C6B73")
PALE_BLUE = colors.HexColor("#EAF2F6")
PALE_TEAL = colors.HexColor("#E7F4F1")
PALE_GOLD = colors.HexColor("#FBF3E2")
PALE_RED = colors.HexColor("#F9EAE7")
LIGHT_GREY = colors.HexColor("#F3F5F6")
RULE = colors.HexColor("#D7DEE2")
WHITE = colors.white

STATUS_COLORS = {
    "externally corroborated": PALE_TEAL,
    "internally reconciled": PALE_BLUE,
    "partially reconciled": PALE_GOLD,
    "unresolved": PALE_RED,
}


def register_font() -> tuple[str, str]:
    """Use DejaVu when available and fall back to built-in Helvetica."""

    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("BriefSans", str(regular)))
        pdfmetrics.registerFont(TTFont("BriefSans-Bold", str(bold)))
        return "BriefSans", "BriefSans-Bold"
    return "Helvetica", "Helvetica-Bold"


BODY_FONT, BOLD_FONT = register_font()


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=9,
            leading=11,
            textColor=TEAL,
            spaceAfter=12,
            tracking=0.8,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName=BOLD_FONT,
            fontSize=30,
            leading=34,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=base["Normal"],
            fontName=BODY_FONT,
            fontSize=13,
            leading=18,
            textColor=MUTED,
            spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName=BOLD_FONT,
            fontSize=18,
            leading=22,
            textColor=NAVY,
            spaceBefore=2,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=BOLD_FONT,
            fontSize=12,
            leading=15,
            textColor=BLUE,
            spaceBefore=9,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=9.2,
            leading=13.5,
            textColor=INK,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=7.4,
            leading=10,
            textColor=MUTED,
        ),
        "table_head": ParagraphStyle(
            "table_head",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=7.2,
            leading=9,
            textColor=WHITE,
        ),
        "table": ParagraphStyle(
            "table",
            parent=base["Normal"],
            fontName=BODY_FONT,
            fontSize=7.1,
            leading=9,
            textColor=INK,
        ),
        "table_bold": ParagraphStyle(
            "table_bold",
            parent=base["Normal"],
            fontName=BOLD_FONT,
            fontSize=7.1,
            leading=9,
            textColor=INK,
        ),
        "callout": ParagraphStyle(
            "callout",
            parent=base["BodyText"],
            fontName=BOLD_FONT,
            fontSize=11,
            leading=15,
            textColor=NAVY,
            spaceAfter=0,
        ),
        "source": ParagraphStyle(
            "source",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=7.4,
            leading=10.5,
            textColor=INK,
            leftIndent=10,
            firstLineIndent=-10,
            spaceAfter=4,
        ),
        "center_small": ParagraphStyle(
            "center_small",
            parent=base["BodyText"],
            fontName=BODY_FONT,
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
    }


S = styles()


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def bullet(text: str) -> Paragraph:
    return p(f"- {text}", "body")


def cover_page(canvas, document) -> None:  # noqa: ANN001
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 0.18 * inch, width, 0.18 * inch, stroke=0, fill=1)
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, width, 0.12 * inch, stroke=0, fill=1)
    canvas.restoreState()


def later_pages(canvas, document) -> None:  # noqa: ANN001
    canvas.saveState()
    width, height = letter
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(0.65 * inch, height - 0.48 * inch, width - 0.65 * inch, height - 0.48 * inch)
    canvas.setFont(BODY_FONT, 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.65 * inch, height - 0.38 * inch, "ELECTION ADMINISTRATION DATA MONITOR")
    canvas.drawRightString(width - 0.65 * inch, 0.38 * inch, f"{document.page}")
    canvas.restoreState()


def stat_card(value: str, label: str, color: colors.Color) -> Table:
    table = Table(
        [[p(value, "callout")], [p(label, "small")]],
        colWidths=[1.95 * inch],
        rowHeights=[0.42 * inch, 0.48 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def candidate_table(review: pd.DataFrame) -> Table:
    ordered = review.sort_values("mail_rejection_rate_pct", ascending=False)
    rows = [
        [
            p("Jurisdiction", "table_head"),
            p("Rate", "table_head"),
            p("State", "table_head"),
            p("Dominant reported reason", "table_head"),
            p("Evidence status", "table_head"),
        ]
    ]
    for _, row in ordered.iterrows():
        dominant = (
            "No reason detail"
            if row["dominant_reason_total"] == 0
            else f"{row['dominant_reported_reason'].capitalize()}<br/>"
            f"{int(row['dominant_reason_total']):,} ({row['dominant_reason_share_pct']:.1f}%)"
        )
        rows.append(
            [
                p(str(row["jurisdiction"]), "table_bold"),
                p(f"{row['mail_rejection_rate_pct']:.2f}%", "table"),
                p(f"{row['state_weighted_rate_pct']:.2f}%", "table"),
                p(dominant, "table"),
                p(str(row["validation_status"]).title(), "table"),
            ]
        )

    table = Table(
        rows,
        colWidths=[1.52 * inch, 0.55 * inch, 0.55 * inch, 1.82 * inch, 1.55 * inch],
        repeatRows=1,
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for index, (_, row) in enumerate(ordered.iterrows(), start=1):
        commands.append(
            ("BACKGROUND", (4, index), (4, index), STATUS_COLORS[row["validation_status"]])
        )
        if index % 2 == 0:
            commands.append(("BACKGROUND", (0, index), (3, index), LIGHT_GREY))
    table.setStyle(TableStyle(commands))
    return table


def evidence_cards(review: pd.DataFrame) -> Table:
    counts = review["validation_status"].value_counts()
    data = [
        [
            stat_card(str(int(counts.get("externally corroborated", 0))), "Externally corroborated", PALE_TEAL),
            stat_card(str(int(counts.get("internally reconciled", 0))), "Internally reconciled", PALE_BLUE),
        ],
        [
            stat_card(str(int(counts.get("partially reconciled", 0))), "Partially reconciled", PALE_GOLD),
            stat_card(str(int(counts.get("unresolved", 0))), "Unresolved", PALE_RED),
        ],
    ]
    table = Table(data, colWidths=[2.05 * inch, 2.05 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def source_link(number: int, title: str, url: str) -> Paragraph:
    return p(f'{number}. <link href="{url}" color="#2D6A8A">{title}</link>', "source")


def build_story(review: pd.DataFrame, triage_summary: dict) -> list:
    mail = triage_summary["mail_rejection_screen"]
    story: list = []

    story.extend(
        [
            Spacer(1, 0.35 * inch),
            p("PORTFOLIO ANALYTICAL BRIEF", "cover_kicker"),
            p("From Outlier to<br/>Review Queue", "cover_title"),
            p(
                "A responsible screen of 2024 election-administration data",
                "cover_subtitle",
            ),
            HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=20),
            Table(
                [
                    [
                        stat_card(f"{mail['modeled_jurisdictions']:,}", "Jurisdictions modeled", PALE_BLUE),
                        stat_card(str(mail["high_priority_review_candidates"]), "Records selected for review", PALE_GOLD),
                        stat_card("0", "Aggregate arithmetic gaps", PALE_TEAL),
                    ]
                ],
                colWidths=[2.05 * inch, 2.05 * inch, 2.05 * inch],
                hAlign="LEFT",
                style=[
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ],
            ),
            Spacer(1, 0.18 * inch),
            p("The result", "h2"),
            p(
                "The statistical screen did not identify a simple data-entry error or establish "
                "misconduct. It produced a documented review queue: one record was independently "
                "corroborated, four were internally reconciled, one was partially reconciled, and "
                "one remained unresolved.",
                "body",
            ),
            Spacer(1, 0.10 * inch),
            p(
                "An outlier is a prompt for contextual review - not evidence of fraud, error, "
                "misconduct, or disenfranchisement.",
                "callout",
            ),
            Spacer(1, 0.45 * inch),
            p("Zuhair Taha", "h2"),
            p("Election Administration Data Monitor | August 2026", "small"),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("1. Screen first, investigate second", "h1"),
            p(
                "The analysis began with 6,461 EAVS jurisdiction records. Quality rules required "
                "at least 500 returned mail ballots, valid rejected-ballot counts, and no material "
                "counted-plus-rejected reconciliation gap. That left 2,621 comparison-eligible "
                "jurisdictions; 2,605 in 43 states and territories had enough same-state peers for "
                "the statistical model.",
            ),
            p("Selection rule", "h2"),
            p(
                "For each state, a beta-binomial model estimated the distribution of rejected "
                "ballots while allowing jurisdiction-level rates to vary. A record entered the "
                "review queue only when its upper-tail probability passed a within-state Bonferroni "
                "threshold and the lower bound of its 95% Wilson interval exceeded the state's "
                "weighted rate.",
            ),
            Image(str(FIGURE_PATH), width=6.85 * inch, height=3.75 * inch),
            p(
                "Figure 1. Rejection rates for the seven records selected for contextual review. "
                "State weighted rates provide within-state context; intervals are 95% Wilson intervals.",
                "center_small",
            ),
            Spacer(1, 0.08 * inch),
            p("Why this matters", "h2"),
            p(
                "A defensible portfolio project does not stop at an outlier score. It checks whether "
                "the source totals reconcile, examines the categories behind the total, and records "
                "what independent official evidence can - and cannot - confirm.",
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("2. Evidence, not labels", "h1"),
            p(
                "All seven candidates pass the aggregate arithmetic check: counted plus rejected "
                "equals returned. Five also have detailed reason counts that exactly reconcile. "
                "The table separates those internal checks from independent corroboration.",
            ),
            candidate_table(review),
            Spacer(1, 0.16 * inch),
            p("Evidence categories", "h2"),
            evidence_cards(review),
            p(
                "Externally corroborated means an official source independently reports a closely "
                "matching jurisdiction-level rate. Internally reconciled means EAVS reason detail "
                "fully accounts for the total and policy context is consistent, but no independent "
                "local count was found. Partial and unresolved labels preserve remaining uncertainty.",
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("3. Context changed the interpretation", "h1"),
            p("Late arrival", "h2"),
            p(
                "Late ballots were the largest reported category in Henderson County, Orleans "
                "Parish, and Scott County. Texas set a regular 7 p.m. Election Day receipt deadline; "
                "Indiana used 6 p.m.; Louisiana required receipt by the applicable deadline and "
                "provided instructions for certificate-envelope completion and cure. These records "
                "support operational questions about ballot-return timing, not allegations about voters.",
            ),
            p("Signature verification and curing", "h2"),
            p(
                "Nonmatching signatures account for 23 of 24 Wheatland County rejections and 121 "
                "of 147 Adams County rejections. EAVS also records ballots entering cure processes. "
                "Montana's official guidance explains how a voter can resolve a rejected ballot. "
                "Washington's annual report independently corroborates Adams County's rate at 2.64% "
                "and identifies signature mismatch as the leading statewide 2024 general-election reason.",
            ),
            p("A label requiring special care", "h2"),
            p(
                "Nashua Ward 5 reports 37 of 45 rejections as 'voter already voted.' The counts "
                "reconcile, but that survey label is not a finding of double voting. New Hampshire "
                "law explicitly governs the interaction between an absentee-voter notation and an "
                "attempt to vote in person.",
            ),
            p("The unresolved record", "h2"),
            p(
                "Noble County reports 39 rejections and exact aggregate arithmetic, but every "
                "detailed reason field is zero. Its official results use a broader 'absentee' category "
                "that includes in-person absentee voting, so that total cannot validate EAVS's mail-only "
                "denominator. The evidence status remains unresolved.",
            ),
            KeepTogether(
                [
                    Spacer(1, 0.08 * inch),
                    Table(
                        [[p(
                            "Responsible conclusion: the screen found administrative patterns and "
                            "reporting questions. It did not establish unlawful conduct or an incorrect election outcome.",
                            "callout",
                        )]],
                        colWidths=[6.55 * inch],
                        style=[
                            ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
                            ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
                            ("LEFTPADDING", (0, 0), (-1, -1), 12),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                            ("TOPPADDING", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                        ],
                    ),
                ]
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            p("4. Limits, next steps, and sources", "h1"),
            p("What this analysis can say", "h2"),
            bullet("It can prioritize reported values for follow-up within a defensible same-state comparison."),
            bullet("It can test aggregate arithmetic and detailed reason reconciliation."),
            bullet("It can distinguish independent corroboration from policy context and missing evidence."),
            p("What it cannot say", "h2"),
            bullet("It cannot determine why an individual ballot was rejected or evaluate a legal decision."),
            bullet("It cannot infer voter intent or establish error, fraud, misconduct, or disenfranchisement."),
            bullet("It cannot make unlike local reporting systems fully comparable."),
            p("Best next step", "h2"),
            p(
                "Request a certified mail-ballot rejection-reason report from Noble County first, "
                "then seek independent jurisdiction-level reports for the four internally reconciled "
                "records. Append responses as new evidence; do not overwrite the source data or the "
                "status used in this version.",
            ),
            p("Selected official sources", "h2"),
            source_link(1, "U.S. Election Assistance Commission - EAVS reports and datasets", "https://www.eac.gov/research-and-data/studies-and-reports"),
            source_link(2, "Indiana Election Division - November 2024 Dispatch", "https://www.in.gov/sos/elections/files/Dispatch.Nov-2024.FINAL.pdf"),
            source_link(3, "Texas Secretary of State - November 5, 2024 Election Law Calendar", "https://www.sos.state.tx.us/elections/laws/advisory2024-17-nov-5-dec-14-2024-election-calendar.shtml"),
            source_link(4, "Louisiana Secretary of State - Absentee Voting FAQs", "https://www.sos.la.gov/elections-voting/absentee-voting-faqs"),
            source_link(5, "Montana Secretary of State - Resolve a Rejected Ballot", "https://votemt.gov/resolve-my-ballot/"),
            source_link(6, "New Hampshire RSA 659:55", "https://gc.nh.gov/rsa/html/LXIII/659/659-55.htm"),
            source_link(7, "Noble County - 2024 General Election Official Results", "https://www.boe.ohio.gov/noble/c/elecres/20241105results.pdf"),
            source_link(8, "Washington Secretary of State - 2024 Annual Elections Report", "https://www.sos.wa.gov/sites/default/files/2025-10/2024%20Annual%20Elections%20Report.pdf"),
            Spacer(1, 0.08 * inch),
            p("Reproducibility", "h2"),
            p(
                "The GitHub repository contains the source manifest, validation rules, statistical "
                "methods, tests, contextual source registry, machine-readable review table, figures, "
                "and the script that generated this brief.",
            ),
            Spacer(1, 0.08 * inch),
            HRFlowable(width="100%", thickness=1, color=RULE, spaceAfter=8),
            p(
                "Bottom line: the project's contribution is the conversion of a statistical outlier "
                "screen into a documented, uncertainty-aware review queue.",
                "callout",
            ),
        ]
    )
    return story


def main() -> None:
    review = pd.read_csv(REVIEW_PATH, dtype={"FIPSCode": "string"})
    triage_summary = json.loads(TRIAGE_SUMMARY_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.58 * inch,
        title="From Outlier to Review Queue",
        author="Zuhair Taha",
        subject="Responsible contextual review of 2024 EAVS mail-ballot rejection rates",
    )
    document.build(
        build_story(review, triage_summary),
        onFirstPage=cover_page,
        onLaterPages=later_pages,
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
