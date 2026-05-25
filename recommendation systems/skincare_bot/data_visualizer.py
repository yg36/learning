from collections import Counter
from datetime import datetime
from pathlib import Path
import re

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


DEFAULT_OUTPUT = Path("visualizedData.pdf")


PALETTE = [
    colors.HexColor("#2563EB"),
    colors.HexColor("#059669"),
    colors.HexColor("#C2410C"),
    colors.HexColor("#7C3AED"),
    colors.HexColor("#DC2626"),
    colors.HexColor("#0891B2"),
]


class HorizontalBarChart(Flowable):
    def __init__(self, title, data, width=7.0 * inch, height=2.6 * inch, color=None, max_items=10):
        super().__init__()
        self.title = title
        self.data = data[:max_items]
        self.width = width
        self.height = height
        self.color = color or PALETTE[0]

    def wrap(self, available_width, available_height):
        self.width = min(self.width, available_width)
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()

        title_y = self.height - 12
        canvas.setFillColor(colors.HexColor("#0F172A"))
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(0, title_y, self.title)

        if not self.data:
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#64748B"))
            canvas.drawString(0, title_y - 18, "No data available")
            canvas.restoreState()
            return

        label_width = min(125, self.width * 0.34)
        value_width = 38
        chart_width = self.width - label_width - value_width - 12
        top = self.height - 34
        row_height = min(14, max(9, (self.height - 42) / len(self.data)))
        max_value = max(value for _, value in self.data) or 1

        canvas.setFont("Helvetica", 7.2)
        for index, (label, value) in enumerate(self.data):
            y = top - index * row_height
            bar_height = row_height * 0.58
            safe_label = _shorten(str(label), 24)

            canvas.setFillColor(colors.HexColor("#334155"))
            canvas.drawString(0, y, safe_label)
            canvas.setFillColor(colors.HexColor("#E2E8F0"))
            canvas.roundRect(label_width, y - 1, chart_width, bar_height, 1.5, stroke=0, fill=1)
            canvas.setFillColor(self.color)
            canvas.roundRect(label_width, y - 1, chart_width * (value / max_value), bar_height, 1.5, stroke=0, fill=1)
            canvas.setFillColor(colors.HexColor("#475569"))
            canvas.drawRightString(label_width + chart_width + value_width, y, _format_number(value))

        canvas.restoreState()


class GroupedScoreChart(Flowable):
    def __init__(self, title, rows, width=7.0 * inch, height=2.8 * inch):
        super().__init__()
        self.title = title
        self.rows = rows
        self.width = width
        self.height = height
        self.series = [
            ("history_affinity_score", "History", PALETTE[0]),
            ("query_match_score", "Query", PALETTE[1]),
            ("recommendation_score", "Recommendation", PALETTE[2]),
        ]

    def wrap(self, available_width, available_height):
        self.width = min(self.width, available_width)
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#0F172A"))
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(0, self.height - 12, self.title)

        legend_x = 0
        for _, label, color in self.series:
            canvas.setFillColor(color)
            canvas.roundRect(legend_x, self.height - 31, 8, 8, 1, stroke=0, fill=1)
            canvas.setFillColor(colors.HexColor("#475569"))
            canvas.setFont("Helvetica", 7.4)
            canvas.drawString(legend_x + 12, self.height - 30, label)
            legend_x += 92

        if not self.rows:
            canvas.drawString(0, self.height - 50, "No score data available")
            canvas.restoreState()
            return

        label_width = 120
        chart_width = self.width - label_width - 42
        top = self.height - 55
        row_height = 19
        bar_height = 3.5

        for row_index, row in enumerate(self.rows):
            y = top - row_index * row_height
            canvas.setFillColor(colors.HexColor("#334155"))
            canvas.setFont("Helvetica", 7.3)
            canvas.drawString(0, y - 1, _shorten(row["category"], 24))

            for series_index, (key, _, color) in enumerate(self.series):
                value = min(float(row.get(key, 0)), 1)
                bar_y = y - series_index * (bar_height + 1.2)
                canvas.setFillColor(colors.HexColor("#E2E8F0"))
                canvas.roundRect(label_width, bar_y, chart_width, bar_height, 1, stroke=0, fill=1)
                canvas.setFillColor(color)
                canvas.roundRect(label_width, bar_y, chart_width * value, bar_height, 1, stroke=0, fill=1)

            canvas.setFillColor(colors.HexColor("#475569"))
            canvas.drawRightString(label_width + chart_width + 38, y - 5, f"{row['recommendation_score']:.2f}")

        canvas.restoreState()


def visualize_dataset(dataset_path, output_path=DEFAULT_OUTPUT):
    dataset_path = Path(dataset_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(dataset_path)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.42 * inch,
        bottomMargin=0.42 * inch,
        title="Skincare Recommendation Dataset Report",
        author="skincare_bot",
    )

    styles = _styles()
    story = []

    story.extend(_cover_page(df, dataset_path, styles))
    story.append(PageBreak())
    story.extend(_catalog_page(df, styles))
    story.append(PageBreak())
    story.extend(_behavior_page(df, styles))
    story.append(PageBreak())
    story.extend(_data_dictionary_page(df, styles))

    doc.build(story, onFirstPage=_page_frame, onLaterPages=_page_frame)
    return output_path


def _cover_page(df, dataset_path, styles):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    metrics = [
        ("Rows", f"{len(df):,}"),
        ("Columns", f"{len(df.columns):,}"),
        ("Unique Products", f"{df['product_title'].nunique():,}"),
        ("Users", f"{df['user_id'].nunique():,}"),
        ("Skincare Rows", _percent((df["product_category"].astype(str).str.lower() == "skincare").mean())),
        ("Avg Rating", f"{df['rating'].mean():.2f}"),
    ]

    story = [
        Paragraph("Skincare Recommendation Dataset Report", styles["ReportTitle"]),
        Paragraph(f"Source: {dataset_path} | Generated: {generated_at}", styles["Subtitle"]),
        Spacer(1, 0.18 * inch),
        _metric_table(metrics),
        Spacer(1, 0.24 * inch),
        _two_column(
            HorizontalBarChart("Product Type Distribution", _top_counts(df, "product_type", 10), color=PALETTE[0]),
            HorizontalBarChart("Skin Type Distribution", _top_counts(df, "skin_type", 8), color=PALETTE[1]),
        ),
        Spacer(1, 0.22 * inch),
        _insight_box(
            "Report Focus",
            [
                "Validates that the active catalog is skincare-only and large enough for personalization tests.",
                "Summarizes coverage for product types, skin types, safety flags, interaction events, and recommendation signals.",
                "Generated before recommendations run so the dataset used by the recommender can be inspected every time.",
            ],
            styles,
        ),
    ]
    return story


def _catalog_page(df, styles):
    score_rows = _average_by_category(
        df,
        category_col="product_type",
        value_cols=["history_affinity_score", "query_match_score", "recommendation_score"],
        limit=10,
    )
    story = [
        Paragraph("Catalog Quality Snapshot", styles["PageTitle"]),
        Paragraph("Coverage, safety flags, price bands, ingredients, and model-affinity signals.", styles["Subtitle"]),
        Spacer(1, 0.12 * inch),
        _two_column(
            HorizontalBarChart("Price Tier Coverage", _top_counts(df, "price_tier", 6), color=PALETTE[2]),
            HorizontalBarChart("Safety Flag Coverage", _flag_counts(df, _safety_columns()), color=PALETTE[3]),
        ),
        Spacer(1, 0.18 * inch),
        _two_column(
            GroupedScoreChart("Average Model Signals By Product Type", score_rows),
            HorizontalBarChart("Top Ingredients", _term_counts(df, "key_ingredients", 12), color=PALETTE[5]),
        ),
    ]
    return story


def _behavior_page(df, styles):
    metrics = [
        ("Avg History Affinity", f"{df['history_affinity_score'].mean():.3f}"),
        ("Avg Query Match", f"{df['query_match_score'].mean():.3f}"),
        ("Avg Personalization", f"{df['personalization_score'].mean():.3f}"),
        ("Avg Recommendation", f"{df['recommendation_score'].mean():.3f}"),
        ("Avg Dwell Sec", f"{df['dwell_time_seconds'].mean():.1f}"),
        ("Avg Scroll Depth", f"{df['scroll_depth'].mean():.1f}%"),
    ]
    story = [
        Paragraph("Behavior And Personalization Snapshot", styles["PageTitle"]),
        Paragraph("Interaction funnel, concern coverage, and history-driven readiness.", styles["Subtitle"]),
        Spacer(1, 0.12 * inch),
        _metric_table(metrics),
        Spacer(1, 0.18 * inch),
        HorizontalBarChart(
            "Interaction Funnel",
            _flag_counts(df, ["shown", "hovered", "clicked", "added_to_cart", "purchased", "wishlisted"]),
            width=10.0 * inch,
            height=2.05 * inch,
            color=PALETTE[0],
        ),
        Spacer(1, 0.18 * inch),
        _two_column(
            HorizontalBarChart("User Concern Coverage", _term_counts(df, "skin_concerns", 10), color=PALETTE[4]),
            HorizontalBarChart("Product Target Concern Coverage", _term_counts(df, "target_concerns", 10), color=PALETTE[1]),
        ),
    ]
    return story


def _data_dictionary_page(df, styles):
    groups = [
        ("User Context", ["user_id", "skin_type", "skin_tone", "sensitivity_level", "acne_prone"]),
        ("Session Context", ["device_type", "weather_condition", "time_of_day", "query", "intent"]),
        ("History", ["previous_queries", "previous_hovered_product_titles", "previous_clicked_tags", "history_affinity_score"]),
        ("Product", ["product_title", "product_type", "key_ingredients", "target_concerns", "product_price"]),
        ("Safety", _safety_columns()),
        ("Model Signals", ["query_match_score", "personalization_score", "recommendation_score", "rank_position"]),
        ("Analytics", ["shown", "hovered", "clicked", "added_to_cart", "purchased", "dwell_time_seconds"]),
    ]

    rows = [["Group", "Columns Present In Dataset"]]
    for group_name, columns in groups:
        present = [column for column in columns if column in df.columns]
        rows.append([group_name, ", ".join(present)])

    table = Table(rows, colWidths=[1.5 * inch, 8.8 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story = [
        Paragraph("Dataset Structure", styles["PageTitle"]),
        Paragraph("High-level column map for engineering and testing.", styles["Subtitle"]),
        Spacer(1, 0.16 * inch),
        table,
        Spacer(1, 0.2 * inch),
        _insight_box(
            "Recommended Use",
            [
                "Use the history columns for behavior-aware ranking and the safety columns as hard constraints.",
                "Use query, concern, ingredient, and product metadata for content-based retrieval when chatbot history is sparse.",
            ],
            styles,
        ),
    ]
    return story


def _page_frame(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, doc.height + doc.bottomMargin + 8, doc.width + doc.leftMargin, doc.height + doc.bottomMargin + 8)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.23 * inch, f"Page {doc.page}")
    canvas.drawString(doc.leftMargin, 0.23 * inch, "skincare_bot data visualization")
    canvas.restoreState()


def _metric_table(metrics):
    cells = []
    row = []
    for label, value in metrics:
        row.append(Paragraph(f"<b>{value}</b><br/><font size='7' color='#64748B'>{label}</font>", _styles()["Metric"]))
        if len(row) == 3:
            cells.append(row)
            row = []
    if row:
        while len(row) < 3:
            row.append("")
        cells.append(row)

    table = Table(cells, colWidths=[3.35 * inch, 3.35 * inch, 3.35 * inch], rowHeights=0.58 * inch)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E2E8F0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def _two_column(left, right):
    table = Table([[left, right]], colWidths=[5.2 * inch, 5.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return table


def _insight_box(title, bullets, styles):
    content = [Paragraph(title, styles["SectionTitle"])]
    for bullet in bullets:
        content.append(Paragraph(f"- {bullet}", styles["SmallText"]))

    table = Table([[content]], colWidths=[10.3 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=27,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_CENTER,
            spaceAfter=5,
        )
    )
    base.add(
        ParagraphStyle(
            "PageTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=3,
        )
    )
    base.add(
        ParagraphStyle(
            "SectionTitle",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#1E3A8A"),
            spaceAfter=4,
        )
    )
    base.add(
        ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            "SmallText",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
            spaceAfter=2,
        )
    )
    base.add(
        ParagraphStyle(
            "Metric",
            parent=base["Normal"],
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0F172A"),
        )
    )
    return base


def _top_counts(df, column, limit=10):
    if column not in df:
        return []
    counts = df[column].fillna("unknown").astype(str).str.lower().value_counts().head(limit)
    return [(label, int(value)) for label, value in counts.items()]


def _flag_counts(df, columns):
    data = []
    for column in columns:
        if column not in df:
            continue
        values = pd.to_numeric(df[column], errors="coerce").fillna(0)
        data.append((column.replace("_", " "), int(values.sum())))
    return data


def _term_counts(df, column, limit=10):
    if column not in df:
        return []
    counter = Counter()
    for value in df[column].dropna():
        for term in re.split(r"[|;,]", str(value)):
            term = term.strip().lower()
            if term:
                counter[term] += 1
    return counter.most_common(limit)


def _average_by_category(df, category_col, value_cols, limit=8):
    if category_col not in df:
        return []
    available_cols = [col for col in value_cols if col in df]
    if not available_cols:
        return []

    working = df[[category_col] + available_cols].copy()
    for col in available_cols:
        working[col] = pd.to_numeric(working[col], errors="coerce")

    grouped = working.groupby(category_col)[available_cols].mean().reset_index()
    grouped = grouped.sort_values(available_cols[-1], ascending=False).head(limit)
    rows = []
    for _, row in grouped.iterrows():
        rows.append({"category": str(row[category_col]), **{col: float(row[col]) for col in available_cols}})
    return rows


def _safety_columns():
    return [
        "alcohol_free",
        "fragrance_free",
        "essential_oil_free",
        "non_comedogenic",
        "pregnancy_safe",
        "vegan",
        "cruelty_free",
    ]


def _percent(value):
    return f"{value * 100:.1f}%"


def _format_number(value):
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.2f}"
    return f"{int(value):,}"


def _shorten(value, limit):
    value = str(value)
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


if __name__ == "__main__":
    output = visualize_dataset("data/skincare_history_catalog_500rows.csv")
    print(f"Wrote {output}")
