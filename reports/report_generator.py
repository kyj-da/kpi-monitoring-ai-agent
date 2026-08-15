from io import BytesIO
import os
import re
import html

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)

from reportlab.graphics.shapes import (
    Drawing,
    String,
)

from reportlab.graphics.charts.lineplots import (
    LinePlot,
)

from reportlab.graphics.charts.legends import (
    Legend,
)


# ==================================================
# Font
# ==================================================

FONT_NAME = "KoreanFont"
FONT_BOLD_NAME = "KoreanFontBold"


def register_korean_font():

    regular_candidates = [
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\malgunsl.ttf",
    ]

    bold_candidates = [
        r"C:\Windows\Fonts\malgunbd.ttf",
        r"C:\Windows\Fonts\malgun.ttf",
    ]

    regular_path = None
    bold_path = None

    for path in regular_candidates:

        if os.path.exists(path):
            regular_path = path
            break

    for path in bold_candidates:

        if os.path.exists(path):
            bold_path = path
            break

    if not regular_path:

        raise FileNotFoundError(
            "PDF 생성을 위한 한글 폰트를 찾지 못했습니다. "
            "Windows의 맑은 고딕 폰트를 확인해주세요."
        )

    if not bold_path:
        bold_path = regular_path

    try:
        pdfmetrics.getFont(
            FONT_NAME
        )

    except KeyError:
        pdfmetrics.registerFont(
            TTFont(
                FONT_NAME,
                regular_path,
            )
        )

    try:
        pdfmetrics.getFont(
            FONT_BOLD_NAME
        )

    except KeyError:
        pdfmetrics.registerFont(
            TTFont(
                FONT_BOLD_NAME,
                bold_path,
            )
        )


# ==================================================
# Styles
# ==================================================

def build_styles():

    styles = (
        getSampleStyleSheet()
    )

    return {

        "title": ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName=FONT_BOLD_NAME,
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#111827"
            ),
            spaceAfter=3 * mm,
        ),

        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName=FONT_NAME,
            fontSize=8.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#6B7280"
            ),
            spaceAfter=7 * mm,
        ),

        "heading": ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName=FONT_BOLD_NAME,
            fontSize=13.5,
            leading=17,
            textColor=colors.HexColor(
                "#111827"
            ),
            spaceBefore=4 * mm,
            spaceAfter=3 * mm,
        ),

        "subheading": ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontName=FONT_BOLD_NAME,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor(
                "#374151"
            ),
            spaceBefore=2.5 * mm,
            spaceAfter=2 * mm,
        ),

        "body": ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName=FONT_NAME,
            fontSize=8.7,
            leading=13.2,
            textColor=colors.HexColor(
                "#374151"
            ),
            spaceAfter=1.3 * mm,
        ),

        "small": ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontName=FONT_NAME,
            fontSize=7.8,
            leading=11,
            textColor=colors.HexColor(
                "#6B7280"
            ),
        ),

        "table_header": ParagraphStyle(
            "TableHeader",
            parent=styles["BodyText"],
            fontName=FONT_BOLD_NAME,
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),

        "table_body": ParagraphStyle(
            "TableBody",
            parent=styles["BodyText"],
            fontName=FONT_NAME,
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#374151"
            ),
        ),

        "highlight_title": ParagraphStyle(
            "HighlightTitle",
            parent=styles["BodyText"],
            fontName=FONT_BOLD_NAME,
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor(
                "#1D4ED8"
            ),
        ),

        "highlight_body": ParagraphStyle(
            "HighlightBody",
            parent=styles["BodyText"],
            fontName=FONT_NAME,
            fontSize=8.5,
            leading=13,
            textColor=colors.HexColor(
                "#1F2937"
            ),
        ),

        "warning": ParagraphStyle(
            "Warning",
            parent=styles["BodyText"],
            fontName=FONT_NAME,
            fontSize=7.8,
            leading=11,
            textColor=colors.HexColor(
                "#6B7280"
            ),
        ),
    }


# ==================================================
# Text Helper
# ==================================================

def safe_text(
    text
):

    if text is None:
        return ""

    return html.escape(
        str(
            text
        )
    )


def clean_markdown(
    text
):

    if not text:
        return ""

    text = re.sub(
        r"#{1,6}\s*",
        "",
        text,
    )

    text = text.replace(
        "**",
        "",
    )

    text = text.replace(
        "__",
        "",
    )

    text = text.replace(
        "`",
        "",
    )

    return text.strip()


# ==================================================
# Agent Result Parsing
# ==================================================

def split_agent_result(
    result
):

    sections = {
        "anomaly": "",
        "cause": "",
        "funnel": "",
        "conclusion": "",
        "caution": "",
    }

    if not result:
        return sections

    mapping = {

        "1. 이상 징후":
            "anomaly",

        "2. 주요 원인 후보":
            "cause",

        "3. Funnel":
            "funnel",

        "4. 결론":
            "conclusion",

        "5. 주의사항":
            "caution",
    }

    current_section = None

    for line in result.splitlines():

        stripped = (
            line.strip()
        )

        matched = False

        for (
            title,
            key,
        ) in mapping.items():

            if stripped.startswith(
                f"## {title}"
            ):

                current_section = key
                matched = True
                break

        if matched:
            continue

        if current_section:

            sections[
                current_section
            ] += (
                line
                + "\n"
            )

    return sections


# ==================================================
# Segment Parsing
# ==================================================

def extract_top_segment(
    cause_text
):

    if not cause_text:
        return None

    match = re.search(
        r"\*\*([A-Za-z]+)\s*×\s*([A-Za-z ]+)\*\*",
        cause_text,
    )

    if not match:
        return None

    return (
        f"{match.group(1).strip()} × "
        f"{match.group(2).strip()}"
    )


def extract_segment_block(
    cause_text,
    segment_name,
):

    if (
        not cause_text
        or not segment_name
    ):
        return ""

    escaped = (
        re.escape(
            segment_name
        )
    )

    pattern = (
        rf"-\s*\*\*{escaped}\*\*"
        rf"(.*?)(?=\n-\s*\*\*|\n→|\Z)"
    )

    match = re.search(
        pattern,
        cause_text,
        re.S | re.I,
    )

    if not match:
        return ""

    return match.group(
        0
    )


def extract_value(
    text,
    keyword,
):

    if not text:
        return "-"

    pattern = (
        rf"{re.escape(keyword)}"
        rf".*?([+-]?[0-9,.]+%?p?)"
    )

    match = re.search(
        pattern,
        text,
        re.S | re.I,
    )

    if not match:
        return "-"

    return match.group(
        1
    )


def extract_section_block(
    cause_text,
    title,
    next_titles=None,
):

    if not cause_text:
        return ""

    if next_titles is None:
        next_titles = []

    if next_titles:

        next_pattern = "|".join(
            re.escape(
                x
            )
            for x in next_titles
        )

        pattern = (
            rf"{re.escape(title)}"
            rf"(.*?)(?={next_pattern}|\Z)"
        )

    else:

        pattern = (
            rf"{re.escape(title)}"
            rf"(.*)\Z"
        )

    match = re.search(
        pattern,
        cause_text,
        re.S | re.I,
    )

    if not match:
        return ""

    return match.group(
        1
    )


def extract_first_segment_name(
    block
):

    if not block:
        return "-"

    match = re.search(
        r"-\s*\*\*([^*]+)\*\*",
        block,
    )

    if not match:
        return "-"

    return (
        match
        .group(1)
        .strip()
    )


def extract_first_contribution(
    block
):

    if not block:
        return "-"

    match = re.search(
        r"Revenue Contribution:"
        r"\s*\*\*?([+-]?[0-9,.]+%)",
        block,
        re.I,
    )

    if not match:
        return "-"

    return match.group(
        1
    )


def get_root_cause_summary(
    cause_text
):

    device_block = (
        extract_section_block(
            cause_text,
            "### Device별",
            [
                "### Landing Page Type별",
                "### 핵심 Device",
            ],
        )
    )

    landing_block = (
        extract_section_block(
            cause_text,
            "### Landing Page Type별",
            [
                "### 핵심 Device",
            ],
        )
    )

    top_segment = (
        extract_top_segment(
            cause_text
        )
    )

    top_segment_block = (
        extract_segment_block(
            cause_text,
            top_segment,
        )
    )

    return [

        {
            "category":
                "디바이스",

            "segment":
                extract_first_segment_name(
                    device_block
                ),

            "contribution":
                extract_first_contribution(
                    device_block
                ),
        },

        {
            "category":
                "랜딩 페이지",

            "segment":
                extract_first_segment_name(
                    landing_block
                ),

            "contribution":
                extract_first_contribution(
                    landing_block
                ),
        },

        {
            "category":
                "교차 세그먼트",

            "segment":
                top_segment
                or "-",

            "contribution":
                extract_value(
                    top_segment_block,
                    "Revenue Contribution",
                ),
        },
    ]


# ==================================================
# Funnel Parsing
# ==================================================

def parse_funnel_rows(
    funnel_text
):

    if not funnel_text:
        return []

    normalized = (
        funnel_text.replace(
            "->",
            "→",
        )
    )

    rows = []

    patterns = [

        (
            "조회 → 장바구니",

            r"View\s*→\s*Cart.*?"
            r"([0-9.]+%).*?"
            r"([+-][0-9.]+%p)",
        ),

        (
            "장바구니 → 결제 시작",

            r"Cart\s*→\s*Checkout.*?"
            r"([0-9.]+%).*?"
            r"([+-][0-9.]+%p)",
        ),

        (
            "결제 시작 → 구매",

            r"Checkout\s*→\s*Purchase.*?"
            r"([0-9.]+%).*?"
            r"([+-][0-9.]+%p)",
        ),

        (
            "전체 구매 전환율",

            r"(?:전체\s*)?Purchase\s*CVR.*?"
            r"([0-9.]+%).*?"
            r"([+-][0-9.]+%p)",
        ),
    ]

    for (
        label,
        pattern,
    ) in patterns:

        match = re.search(
            pattern,
            normalized,
            re.S | re.I,
        )

        if match:

            rows.append(
                [
                    label,
                    match.group(
                        1
                    ),
                    match.group(
                        2
                    ),
                ]
            )

    return rows


def extract_funnel_notes(
    funnel_text
):

    if not funnel_text:
        return []

    notes = []

    for line in (
        clean_markdown(
            funnel_text
        )
        .splitlines()
    ):

        line = (
            line.strip()
        )

        if not line:
            continue

        if line.startswith(
            "|"
        ):
            continue

        if line.startswith(
            "- "
        ):

            notes.append(
                line[
                    2:
                ].strip()
            )

    return notes


# ==================================================
# Table Style
# ==================================================

def apply_standard_table_style(
    table
):

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#374151"
                    ),
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor(
                        "#D1D5DB"
                    ),
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor(
                            "#F8FAFC"
                        ),
                    ],
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )


# ==================================================
# Footer
# ==================================================

def add_page_number(
    canvas,
    doc,
):

    canvas.saveState()

    canvas.setFont(
        FONT_NAME,
        7.2,
    )

    canvas.setFillColor(
        colors.HexColor(
            "#9CA3AF"
        )
    )

    canvas.drawString(
        15 * mm,
        9 * mm,
        "KPI Monitoring AI Agent",
    )

    canvas.drawRightString(
        A4[
            0
        ]
        - 15 * mm,
        9 * mm,
        f"Page {canvas.getPageNumber()}",
    )

    canvas.restoreState()


# ==================================================
# Weekly Trend Chart
# ==================================================

def create_weekly_index_chart(
    weekly_df
):

    df = (
        weekly_df
        .copy()
        .sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )

    if df.empty:
        return None

    if len(
        df
    ) < 2:
        return None

    first_sessions = float(
        df.loc[
            0,
            "sessions"
        ]
    )

    first_cvr = float(
        df.loc[
            0,
            "purchase_cvr_pct"
        ]
    )

    first_revenue = float(
        df.loc[
            0,
            "validated_revenue"
        ]
    )

    if (
        first_sessions <= 0
        or first_cvr <= 0
        or first_revenue <= 0
    ):
        return None

    df[
        "sessions_index"
    ] = (
        df[
            "sessions"
        ]
        / first_sessions
        * 100
    )

    df[
        "cvr_index"
    ] = (
        df[
            "purchase_cvr_pct"
        ]
        / first_cvr
        * 100
    )

    df[
        "revenue_index"
    ] = (
        df[
            "validated_revenue"
        ]
        / first_revenue
        * 100
    )

    drawing = Drawing(
        470,
        185,
    )

    chart = LinePlot()

    chart.x = 45
    chart.y = 35
    chart.width = 365
    chart.height = 115

    x_values = list(
        range(
            len(
                df
            )
        )
    )

    chart.data = [

        [
            (
                x,
                float(
                    y
                ),
            )
            for (
                x,
                y,
            ) in zip(
                x_values,
                df[
                    "sessions_index"
                ],
            )
        ],

        [
            (
                x,
                float(
                    y
                ),
            )
            for (
                x,
                y,
            ) in zip(
                x_values,
                df[
                    "cvr_index"
                ],
            )
        ],

        [
            (
                x,
                float(
                    y
                ),
            )
            for (
                x,
                y,
            ) in zip(
                x_values,
                df[
                    "revenue_index"
                ],
            )
        ],
    ]

    chart.lines[
        0
    ].strokeColor = colors.HexColor(
        "#2563EB"
    )

    chart.lines[
        0
    ].strokeWidth = 1.7

    chart.lines[
        1
    ].strokeColor = colors.HexColor(
        "#16A34A"
    )

    chart.lines[
        1
    ].strokeWidth = 1.7

    chart.lines[
        2
    ].strokeColor = colors.HexColor(
        "#EA580C"
    )

    chart.lines[
        2
    ].strokeWidth = 1.7

    chart.xValueAxis.valueMin = 0

    chart.xValueAxis.valueMax = (
        len(
            df
        )
        - 1
    )

    chart.xValueAxis.valueSteps = (
        x_values
    )

    chart.xValueAxis.labelTextFormat = (
        lambda x:
            df.loc[
                int(
                    x
                ),
                "date"
            ].strftime(
                "%m-%d"
            )
    )

    all_values = (
        df[
            [
                "sessions_index",
                "cvr_index",
                "revenue_index",
            ]
        ]
        .values
        .flatten()
    )

    y_max = float(
        max(
            all_values
        )
    )

    y_axis_max = max(
        200,
        int(
            y_max
            / 100
            + 1
        )
        * 100,
    )

    chart.yValueAxis.valueMin = 0

    chart.yValueAxis.valueMax = (
        y_axis_max
    )

    chart.yValueAxis.valueSteps = list(
        range(
            0,
            y_axis_max
            + 1,
            100,
        )
    )

    drawing.add(
        chart
    )

    drawing.add(
        String(
            45,
            163,
            "주간 KPI 변화 지수 (첫날 = 100)",
            fontName=FONT_BOLD_NAME,
            fontSize=9,
            fillColor=colors.HexColor(
                "#374151"
            ),
        )
    )

    legend = Legend()

    legend.x = 265
    legend.y = 168

    legend.fontName = FONT_NAME
    legend.fontSize = 6.5

    legend.dx = 6
    legend.dy = 6

    legend.deltax = 58
    legend.deltay = 0

    legend.columnMaximum = 3

    legend.colorNamePairs = [

        (
            colors.HexColor(
                "#2563EB"
            ),
            "세션",
        ),

        (
            colors.HexColor(
                "#16A34A"
            ),
            "구매 CVR",
        ),

        (
            colors.HexColor(
                "#EA580C"
            ),
            "매출",
        ),
    ]

    drawing.add(
        legend
    )

    return drawing


# ==================================================
# Daily Report
# ==================================================

def create_daily_report_pdf(
    target_date: str,
    daily_row,
    agent_result: str | None = None,
):

    register_korean_font()

    styles = (
        build_styles()
    )

    buffer = (
        BytesIO()
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=17 * mm,
        title=(
            f"KPI Monitoring Daily Report "
            f"{target_date}"
        ),
        author="KPI Monitoring AI Agent",
    )

    story = []

    revenue_valid = bool(
        daily_row[
            "revenue_data_valid"
        ]
    )

    sections = (
        split_agent_result(
            agent_result
        )
        if agent_result
        else {
            "anomaly": "",
            "cause": "",
            "funnel": "",
            "conclusion": "",
            "caution": "",
        }
    )


    # ==================================================
    # Header
    # ==================================================

    story.append(
        Paragraph(
            "KPI Monitoring Daily Report",
            styles[
                "title"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                f"분석 기준일: "
                f"{safe_text(target_date)}"
                " &nbsp;&nbsp;|&nbsp;&nbsp; "
                "Data Source: BigQuery"
            ),
            styles[
                "subtitle"
            ],
        )
    )


    # ==================================================
    # Executive Summary
    # ==================================================

    story.append(
        Paragraph(
            "Executive Summary",
            styles[
                "heading"
            ],
        )
    )

    anomaly_count = int(
        daily_row[
            "anomaly_count"
        ]
    )

    executive_table = Table(
        [
            [
                Paragraph(
                    "이상 지표",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "AI 원인 분석",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "Revenue 데이터",
                    styles[
                        "table_header"
                    ],
                ),
            ],

            [
                Paragraph(
                    f"{anomaly_count}개",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "완료"
                        if agent_result
                        else "미실행"
                    ),
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "유효"
                        if revenue_valid
                        else "분석 제외"
                    ),
                    styles[
                        "table_body"
                    ],
                ),
            ],
        ],
        colWidths=[
            55 * mm,
            55 * mm,
            55 * mm,
        ],
    )

    apply_standard_table_style(
        executive_table
    )

    story.append(
        executive_table
    )

    story.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )


    # ==================================================
    # Highlight
    # ==================================================

    if agent_result:

        top_segment = (
            extract_top_segment(
                sections[
                    "cause"
                ]
            )
        )

        segment_block = (
            extract_segment_block(
                sections[
                    "cause"
                ],
                top_segment,
            )
        )

        contribution = (
            extract_value(
                segment_block,
                "Revenue Contribution",
            )
        )

        session_change = (
            extract_value(
                segment_block,
                "Sessions 변화",
            )
        )

        cvr_change = (
            extract_value(
                segment_block,
                "Purchase CVR 변화",
            )
        )

        conclusion = (
            clean_markdown(
                sections[
                    "conclusion"
                ]
            )
        )

        highlight_content = [

            Paragraph(
                "주요 영향 구간",
                styles[
                    "highlight_title"
                ],
            ),

            Spacer(
                1,
                1 * mm,
            ),

            Paragraph(
                (
                    f"<b>{safe_text(top_segment or '-')}</b>"
                    f" &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"매출 변화 기여 "
                    f"{safe_text(contribution)}"
                    f" &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"세션 변화 "
                    f"{safe_text(session_change)}"
                    f" &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"구매 전환율 변화 "
                    f"{safe_text(cvr_change)}"
                ),
                styles[
                    "highlight_body"
                ],
            ),
        ]

        if conclusion:

            highlight_content.extend(
                [
                    Spacer(
                        1,
                        2 * mm,
                    ),

                    Paragraph(
                        safe_text(
                            conclusion
                        ),
                        styles[
                            "highlight_body"
                        ],
                    ),
                ]
            )

        highlight_table = Table(
            [
                [
                    highlight_content
                ]
            ],
            colWidths=[
                165 * mm
            ],
        )

        highlight_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor(
                            "#EFF6FF"
                        ),
                    ),

                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.HexColor(
                            "#BFDBFE"
                        ),
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        story.append(
            highlight_table
        )


    # ==================================================
    # 1. KPI Summary
    # ==================================================

    story.append(
        Paragraph(
            "1. 핵심 KPI 요약",
            styles[
                "heading"
            ],
        )
    )

    revenue_text = (
        f"{float(daily_row['validated_revenue']):,.0f}"
        if revenue_valid
        else "분석 제외"
    )

    kpi_data = [

        [
            Paragraph(
                "지표",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "현재 값",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "7일 평균 대비",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "이상 점수",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "상태",
                styles[
                    "table_header"
                ],
            ),
        ],

        [
            Paragraph(
                "세션 수",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{int(daily_row['sessions']):,}",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['sessions_avg_deviation_pct']):+.2f}%",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['sessions_zscore']):.2f}",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                (
                    "이상"
                    if bool(
                        daily_row[
                            "sessions_anomaly"
                        ]
                    )
                    else "정상"
                ),
                styles[
                    "table_body"
                ],
            ),
        ],

        [
            Paragraph(
                "조회 → 장바구니",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['view_to_cart_pct']):.2f}%",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['view_to_cart_avg_deviation_pct']):+.2f}%",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['view_to_cart_zscore']):.2f}",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                (
                    "이상"
                    if bool(
                        daily_row[
                            "view_to_cart_anomaly"
                        ]
                    )
                    else "정상"
                ),
                styles[
                    "table_body"
                ],
            ),
        ],

        [
            Paragraph(
                "구매 전환율",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['purchase_cvr_pct']):.2f}%",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['purchase_cvr_avg_deviation_pct']):+.2f}%",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                f"{float(daily_row['purchase_cvr_zscore']):.2f}",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                (
                    "이상"
                    if bool(
                        daily_row[
                            "purchase_cvr_anomaly"
                        ]
                    )
                    else "정상"
                ),
                styles[
                    "table_body"
                ],
            ),
        ],

        [
            Paragraph(
                "유효 매출",
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                revenue_text,
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                (
                    f"{float(daily_row['revenue_avg_deviation_pct']):+.2f}%"
                    if revenue_valid
                    else "-"
                ),
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                (
                    f"{float(daily_row['revenue_zscore']):.2f}"
                    if revenue_valid
                    else "-"
                ),
                styles[
                    "table_body"
                ],
            ),

            Paragraph(
                (
                    "이상"
                    if (
                        revenue_valid
                        and bool(
                            daily_row[
                                "revenue_anomaly"
                            ]
                        )
                    )
                    else (
                        "정상"
                        if revenue_valid
                        else "분석 제외"
                    )
                ),
                styles[
                    "table_body"
                ],
            ),
        ],
    ]

    kpi_table = Table(
        kpi_data,
        colWidths=[
            42 * mm,
            28 * mm,
            36 * mm,
            27 * mm,
            27 * mm,
        ],
        repeatRows=1,
    )

    apply_standard_table_style(
        kpi_table
    )

    story.append(
        kpi_table
    )


    # ==================================================
    # 2. Anomaly
    # ==================================================

    story.append(
        Paragraph(
            "2. 이상 징후",
            styles[
                "heading"
            ],
        )
    )

    anomalies = []

    anomaly_configs = [

        (
            "세션 수",
            "sessions_anomaly",
            "sessions_avg_deviation_pct",
            "sessions_zscore",
        ),

        (
            "조회 → 장바구니 전환율",
            "view_to_cart_anomaly",
            "view_to_cart_avg_deviation_pct",
            "view_to_cart_zscore",
        ),

        (
            "구매 전환율",
            "purchase_cvr_anomaly",
            "purchase_cvr_avg_deviation_pct",
            "purchase_cvr_zscore",
        ),
    ]

    for (
        metric_name,
        anomaly_col,
        deviation_col,
        score_col,
    ) in anomaly_configs:

        if bool(
            daily_row[
                anomaly_col
            ]
        ):

            anomalies.append(
                (
                    metric_name,
                    float(
                        daily_row[
                            deviation_col
                        ]
                    ),
                    float(
                        daily_row[
                            score_col
                        ]
                    ),
                )
            )

    if (
        revenue_valid
        and bool(
            daily_row[
                "revenue_anomaly"
            ]
        )
    ):

        anomalies.append(
            (
                "유효 매출",
                float(
                    daily_row[
                        "revenue_avg_deviation_pct"
                    ]
                ),
                float(
                    daily_row[
                        "revenue_zscore"
                    ]
                ),
            )
        )

    if anomalies:

        anomaly_table_data = [
            [
                Paragraph(
                    "지표",
                    styles[
                        "table_header"
                    ],
                ),
                Paragraph(
                    "상태",
                    styles[
                        "table_header"
                    ],
                ),
                Paragraph(
                    "7일 평균 대비",
                    styles[
                        "table_header"
                    ],
                ),
                Paragraph(
                    "이상 점수",
                    styles[
                        "table_header"
                    ],
                ),
            ]
        ]

        for (
            metric,
            deviation,
            score,
        ) in anomalies:

            anomaly_table_data.append(
                [
                    Paragraph(
                        safe_text(
                            metric
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        (
                            "이상 상승"
                            if score > 0
                            else "이상 하락"
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        f"{deviation:+.2f}%",
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        f"{score:.2f}",
                        styles[
                            "table_body"
                        ],
                    ),
                ]
            )

        anomaly_table = Table(
            anomaly_table_data,
            colWidths=[
                55 * mm,
                35 * mm,
                42 * mm,
                28 * mm,
            ],
            repeatRows=1,
        )

        apply_standard_table_style(
            anomaly_table
        )

        story.append(
            anomaly_table
        )

    else:

        story.append(
            Paragraph(
                "선택한 날짜에는 핵심 KPI 이상 징후가 감지되지 않았습니다.",
                styles[
                    "body"
                ],
            )
        )


    # ==================================================
    # 3. AI RCA
    # ==================================================

    story.append(
        Paragraph(
            "3. AI 원인 분석",
            styles[
                "heading"
            ],
        )
    )

    if not agent_result:

        story.append(
            Paragraph(
                (
                    "해당 날짜에는 저장된 AI 원인 분석 결과가 없습니다. "
                    "핵심 지표 모니터링 화면에서 AI 원인 분석을 실행하면 "
                    "Daily Report에 분석 결과가 포함됩니다."
                ),
                styles[
                    "body"
                ],
            )
        )

    else:

        cause_rows = (
            get_root_cause_summary(
                sections[
                    "cause"
                ]
            )
        )

        cause_table_data = [
            [
                Paragraph(
                    "분석 구분",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "주요 영향 구간",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "매출 변화 기여",
                    styles[
                        "table_header"
                    ],
                ),
            ]
        ]

        for row_data in cause_rows:

            cause_table_data.append(
                [
                    Paragraph(
                        safe_text(
                            row_data[
                                "category"
                            ]
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        safe_text(
                            row_data[
                                "segment"
                            ]
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        safe_text(
                            row_data[
                                "contribution"
                            ]
                        ),
                        styles[
                            "table_body"
                        ],
                    ),
                ]
            )

        cause_table = Table(
            cause_table_data,
            colWidths=[
                48 * mm,
                65 * mm,
                47 * mm,
            ],
            repeatRows=1,
        )

        apply_standard_table_style(
            cause_table
        )

        story.append(
            cause_table
        )

        top_segment = (
            extract_top_segment(
                sections[
                    "cause"
                ]
            )
        )

        segment_block = (
            extract_segment_block(
                sections[
                    "cause"
                ],
                top_segment,
            )
        )

        session_change = (
            extract_value(
                segment_block,
                "Sessions 변화",
            )
        )

        cvr_change = (
            extract_value(
                segment_block,
                "Purchase CVR 변화",
            )
        )

        story.append(
            Spacer(
                1,
                2 * mm,
            )
        )

        key_segment_table = Table(
            [
                [
                    Paragraph(
                        "핵심 세그먼트",
                        styles[
                            "table_header"
                        ],
                    ),

                    Paragraph(
                        "세션 변화",
                        styles[
                            "table_header"
                        ],
                    ),

                    Paragraph(
                        "구매 전환율 변화",
                        styles[
                            "table_header"
                        ],
                    ),
                ],

                [
                    Paragraph(
                        safe_text(
                            top_segment
                            or "-"
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        safe_text(
                            session_change
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        safe_text(
                            cvr_change
                        ),
                        styles[
                            "table_body"
                        ],
                    ),
                ],
            ],
            colWidths=[
                70 * mm,
                45 * mm,
                45 * mm,
            ],
        )

        apply_standard_table_style(
            key_segment_table
        )

        story.append(
            key_segment_table
        )

        funnel_rows = (
            parse_funnel_rows(
                sections[
                    "funnel"
                ]
            )
        )

        if funnel_rows:

            funnel_block = [

                Paragraph(
                    "핵심 세그먼트 퍼널 변화",
                    styles[
                        "subheading"
                    ],
                )
            ]

            funnel_data = [
                [
                    Paragraph(
                        "퍼널 단계",
                        styles[
                            "table_header"
                        ],
                    ),

                    Paragraph(
                        "당일",
                        styles[
                            "table_header"
                        ],
                    ),

                    Paragraph(
                        "7일 평균 대비",
                        styles[
                            "table_header"
                        ],
                    ),
                ]
            ]

            for row_data in funnel_rows:

                funnel_data.append(
                    [
                        Paragraph(
                            safe_text(
                                row_data[
                                    0
                                ]
                            ),
                            styles[
                                "table_body"
                            ],
                        ),

                        Paragraph(
                            safe_text(
                                row_data[
                                    1
                                ]
                            ),
                            styles[
                                "table_body"
                            ],
                        ),

                        Paragraph(
                            safe_text(
                                row_data[
                                    2
                                ]
                            ),
                            styles[
                                "table_body"
                            ],
                        ),
                    ]
                )

            funnel_table = Table(
                funnel_data,
                colWidths=[
                    72 * mm,
                    42 * mm,
                    46 * mm,
                ],
                repeatRows=1,
            )

            apply_standard_table_style(
                funnel_table
            )

            funnel_block.append(
                funnel_table
            )

            funnel_notes = (
                extract_funnel_notes(
                    sections[
                        "funnel"
                    ]
                )
            )

            if funnel_notes:

                funnel_block.append(
                    Spacer(
                        1,
                        1.5 * mm,
                    )
                )

                for note in funnel_notes:

                    funnel_block.append(
                        Paragraph(
                            "• "
                            + safe_text(
                                note
                            ),
                            styles[
                                "body"
                            ],
                        )
                    )

            story.append(
                KeepTogether(
                    funnel_block
                )
            )

        conclusion = (
            clean_markdown(
                sections[
                    "conclusion"
                ]
            )
        )

        if conclusion:

            story.append(
                Paragraph(
                    "분석 결론",
                    styles[
                        "subheading"
                    ],
                )
            )

            story.append(
                Paragraph(
                    safe_text(
                        conclusion
                    ),
                    styles[
                        "body"
                    ],
                )
            )


    # ==================================================
    # 4. Data Quality
    # ==================================================

    story.append(
        Paragraph(
            "4. 데이터 품질",
            styles[
                "heading"
            ],
        )
    )

    history_days = int(
        daily_row[
            "history_day_count"
        ]
    )

    revenue_valid_days = int(
        daily_row[
            "revenue_valid_day_count"
        ]
    )

    quality_table = Table(
        [
            [
                Paragraph(
                    "점검 항목",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "현재 상태",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "판정",
                    styles[
                        "table_header"
                    ],
                ),
            ],

            [
                Paragraph(
                    "기준 데이터 일수",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{history_days}일",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "충족"
                        if history_days >= 7
                        else "미충족"
                    ),
                    styles[
                        "table_body"
                    ],
                ),
            ],

            [
                Paragraph(
                    "Revenue 유효 기준 일수",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{revenue_valid_days}일",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "충족"
                        if revenue_valid_days >= 7
                        else "미충족"
                    ),
                    styles[
                        "table_body"
                    ],
                ),
            ],

            [
                Paragraph(
                    "Revenue 데이터",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "유효"
                        if revenue_valid
                        else "분석 제외"
                    ),
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "충족"
                        if revenue_valid
                        else "미충족"
                    ),
                    styles[
                        "table_body"
                    ],
                ),
            ],
        ],
        colWidths=[
            70 * mm,
            47 * mm,
            43 * mm,
        ],
        repeatRows=1,
    )

    apply_standard_table_style(
        quality_table
    )

    story.append(
        quality_table
    )


    # ==================================================
    # 5. Method
    # ==================================================

    story.append(
        Paragraph(
            "5. 분석 기준",
            styles[
                "heading"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "이상 탐지는 선택한 날짜 이전의 최근 7일 데이터를 "
                "기준으로 수행합니다. "
                "|Z-score| ≥ 2.0과 "
                "|최근 7일 평균 대비 편차| ≥ 30%를 "
                "동시에 충족한 경우 이상 징후로 판정합니다."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "매출은 유효한 transaction_id를 기준으로 검증한 "
                "Validated Revenue를 사용하며, Transaction Coverage 기준을 "
                "충족한 경우에만 매출 이상 탐지에 포함합니다."
            ),
            styles[
                "body"
            ],
        )
    )

    caution_text = (
        clean_markdown(
            sections[
                "caution"
            ]
        )
    )

    if not caution_text:

        caution_text = (
            "본 리포트의 AI 분석은 KPI 변화에 대한 주요 원인 후보와 "
            "기여도가 높은 세그먼트를 제시합니다. "
            "프로모션, UI 변경, 마케팅 활동, 장애 등 실제 비즈니스 원인은 "
            "본 데이터만으로 확정하지 않습니다."
        )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    caution_table = Table(
        [
            [
                Paragraph(
                    (
                        "<b>분석 해석 시 유의사항</b><br/>"
                        + safe_text(
                            caution_text
                        )
                    ),
                    styles[
                        "warning"
                    ],
                )
            ]
        ],
        colWidths=[
            165 * mm
        ],
    )

    caution_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F3F4F6"
                    ),
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D1D5DB"
                    ),
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(
        caution_table
    )

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf_bytes = (
        buffer.getvalue()
    )

    buffer.close()

    return pdf_bytes


# ==================================================
# Weekly Report
# ==================================================

def create_weekly_report_pdf(
    weekly_df,
    start_date: str,
    end_date: str,
    issue_date: str | None = None,
    issue_agent_result: str | None = None,
):

    register_korean_font()

    styles = (
        build_styles()
    )

    buffer = (
        BytesIO()
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=17 * mm,
        title=(
            f"KPI Monitoring Weekly Report "
            f"{start_date} ~ {end_date}"
        ),
        author="KPI Monitoring AI Agent",
    )

    story = []

    df = (
        weekly_df
        .copy()
        .sort_values(
            "date"
        )
        .reset_index(
            drop=True
        )
    )

    total_days = len(
        df
    )

    total_sessions = int(
        df[
            "sessions"
        ].sum()
    )

    estimated_purchase_sessions = (
        df[
            "sessions"
        ]
        * df[
            "purchase_cvr_pct"
        ]
        / 100
    ).sum()

    weekly_purchase_cvr = (
        estimated_purchase_sessions
        / total_sessions
        * 100
        if total_sessions > 0
        else 0
    )

    valid_revenue_df = (
        df[
            df[
                "revenue_data_valid"
            ] == True
        ]
        .copy()
    )

    total_revenue = float(
        valid_revenue_df[
            "validated_revenue"
        ].sum()
    )

    revenue_valid_days = int(
        df[
            "revenue_data_valid"
        ].sum()
    )

    anomaly_days = int(
        df[
            "any_anomaly"
        ].sum()
    )

    anomaly_ready_days = int(
        (
            df[
                "history_day_count"
            ] >= 7
        ).sum()
    )


    # ==================================================
    # Header
    # ==================================================

    story.append(
        Paragraph(
            "KPI Monitoring Weekly Report",
            styles[
                "title"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                f"분석 기간: "
                f"{safe_text(start_date)} ~ "
                f"{safe_text(end_date)}"
                " &nbsp;&nbsp;|&nbsp;&nbsp; "
                "Data Source: BigQuery"
            ),
            styles[
                "subtitle"
            ],
        )
    )


    # ==================================================
    # Executive Summary
    # ==================================================

    story.append(
        Paragraph(
            "Executive Summary",
            styles[
                "heading"
            ],
        )
    )

    executive_table = Table(
        [
            [
                Paragraph(
                    "총 세션",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "주간 구매 전환율",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "총 유효 매출",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "이상 발생일",
                    styles[
                        "table_header"
                    ],
                ),
            ],

            [
                Paragraph(
                    f"{total_sessions:,}",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{weekly_purchase_cvr:.2f}%",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{total_revenue:,.0f}",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{anomaly_days}일",
                    styles[
                        "table_body"
                    ],
                ),
            ],
        ],
        colWidths=[
            41 * mm,
            41 * mm,
            41 * mm,
            41 * mm,
        ],
    )

    apply_standard_table_style(
        executive_table
    )

    story.append(
        executive_table
    )


    # ==================================================
    # Weekly Main Issue
    # ==================================================

    if issue_date:

        issue_top_segment = None

        if issue_agent_result:

            issue_sections = (
                split_agent_result(
                    issue_agent_result
                )
            )

            issue_top_segment = (
                extract_top_segment(
                    issue_sections[
                        "cause"
                    ]
                )
            )

        highlight_items = [

            Paragraph(
                "주간 주요 이슈",
                styles[
                    "highlight_title"
                ],
            ),

            Spacer(
                1,
                1 * mm,
            ),

            Paragraph(
                (
                    f"<b>{safe_text(issue_date)}</b>"
                    + (
                        f" &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"주요 영향 구간 "
                        f"{safe_text(issue_top_segment)}"
                        if issue_top_segment
                        else ""
                    )
                ),
                styles[
                    "highlight_body"
                ],
            ),
        ]

        highlight_table = Table(
            [
                [
                    highlight_items
                ]
            ],
            colWidths=[
                164 * mm
            ],
        )

        highlight_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor(
                            "#EFF6FF"
                        ),
                    ),

                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.HexColor(
                            "#BFDBFE"
                        ),
                    ),

                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),

                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        9,
                    ),

                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),

                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        story.append(
            highlight_table
        )


    # ==================================================
    # Weekly KPI Trend
    # ==================================================

    weekly_chart = (
        create_weekly_index_chart(
            df
        )
    )

    if weekly_chart:

        story.append(
            Paragraph(
                "주간 KPI 추이",
                styles[
                    "heading"
                ],
            )
        )

        story.append(
            weekly_chart
        )

        story.append(
            Paragraph(
                (
                    "각 KPI는 분석 기간 첫날을 100으로 환산하여 "
                    "상대적인 변화폭을 비교합니다."
                ),
                styles[
                    "small"
                ],
            )
        )


    # ==================================================
    # 1. Daily KPI
    # ==================================================

    story.append(
        Paragraph(
            "1. 일별 KPI 현황",
            styles[
                "heading"
            ],
        )
    )

    daily_table_data = [
        [
            Paragraph(
                "날짜",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "세션",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "구매 전환율",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "유효 매출",
                styles[
                    "table_header"
                ],
            ),

            Paragraph(
                "이상 지표",
                styles[
                    "table_header"
                ],
            ),
        ]
    ]

    for _, row in df.iterrows():

        date_text = (
            row[
                "date"
            ].strftime(
                "%Y-%m-%d"
            )
        )

        revenue_text = (
            f"{float(row['validated_revenue']):,.0f}"
            if bool(
                row[
                    "revenue_data_valid"
                ]
            )
            else "-"
        )

        daily_table_data.append(
            [
                Paragraph(
                    date_text,
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{int(row['sessions']):,}",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{float(row['purchase_cvr_pct']):.2f}%",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    revenue_text,
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    f"{int(row['anomaly_count'])}개",
                    styles[
                        "table_body"
                    ],
                ),
            ]
        )

    daily_table = Table(
        daily_table_data,
        colWidths=[
            35 * mm,
            31 * mm,
            35 * mm,
            35 * mm,
            28 * mm,
        ],
        repeatRows=1,
    )

    apply_standard_table_style(
        daily_table
    )

    story.append(
        daily_table
    )


    # ==================================================
    # 2. Weekly Anomaly
    # ==================================================

    anomaly_rows = []

    anomaly_configs = [

        (
            "세션 수",
            "sessions_anomaly",
            "sessions_zscore",
        ),

        (
            "조회 → 장바구니 전환율",
            "view_to_cart_anomaly",
            "view_to_cart_zscore",
        ),

        (
            "구매 전환율",
            "purchase_cvr_anomaly",
            "purchase_cvr_zscore",
        ),
    ]

    for _, row in df.iterrows():

        date_text = (
            row[
                "date"
            ].strftime(
                "%Y-%m-%d"
            )
        )

        for (
            metric_name,
            anomaly_col,
            score_col,
        ) in anomaly_configs:

            if bool(
                row[
                    anomaly_col
                ]
            ):

                score = float(
                    row[
                        score_col
                    ]
                )

                anomaly_rows.append(
                    [
                        date_text,
                        metric_name,
                        (
                            "이상 상승"
                            if score > 0
                            else "이상 하락"
                        ),
                        f"{score:.2f}",
                    ]
                )

        if (
            bool(
                row[
                    "revenue_data_valid"
                ]
            )
            and bool(
                row[
                    "revenue_anomaly"
                ]
            )
        ):

            score = float(
                row[
                    "revenue_zscore"
                ]
            )

            anomaly_rows.append(
                [
                    date_text,
                    "유효 매출",
                    (
                        "이상 상승"
                        if score > 0
                        else "이상 하락"
                    ),
                    f"{score:.2f}",
                ]
            )

    if anomaly_rows:

        anomaly_table_data = [
            [
                Paragraph(
                    "날짜",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "지표",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "상태",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "이상 점수",
                    styles[
                        "table_header"
                    ],
                ),
            ]
        ]

        for row_data in anomaly_rows:

            anomaly_table_data.append(
                [
                    Paragraph(
                        safe_text(
                            row_data[
                                0
                            ]
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        safe_text(
                            row_data[
                                1
                            ]
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        safe_text(
                            row_data[
                                2
                            ]
                        ),
                        styles[
                            "table_body"
                        ],
                    ),

                    Paragraph(
                        safe_text(
                            row_data[
                                3
                            ]
                        ),
                        styles[
                            "table_body"
                        ],
                    ),
                ]
            )

        anomaly_table = Table(
            anomaly_table_data,
            colWidths=[
                43 * mm,
                55 * mm,
                36 * mm,
                30 * mm,
            ],
            repeatRows=1,
        )

        apply_standard_table_style(
            anomaly_table
        )

        # 제목 + 표 전체를 같이 이동
        weekly_anomaly_block = [
            Paragraph(
                "2. 주간 이상 징후",
                styles[
                    "heading"
                ],
            ),
            anomaly_table,
        ]

        story.append(
            KeepTogether(
                weekly_anomaly_block
            )
        )

    else:

        story.append(
            KeepTogether(
                [
                    Paragraph(
                        "2. 주간 이상 징후",
                        styles[
                            "heading"
                        ],
                    ),

                    Paragraph(
                        (
                            "해당 기간에는 핵심 KPI 이상 징후가 "
                            "감지되지 않았습니다."
                        ),
                        styles[
                            "body"
                        ],
                    ),
                ]
            )
        )


    # ==================================================
    # 3. Main Issue
    # ==================================================

    story.append(
        Paragraph(
            "3. 주요 이슈",
            styles[
                "heading"
            ],
        )
    )

    if issue_date:

        story.append(
            Paragraph(
                (
                    f"주간 내 우선 확인 대상은 "
                    f"<b>{safe_text(issue_date)}</b>입니다."
                ),
                styles[
                    "body"
                ],
            )
        )

        if issue_agent_result:

            issue_sections = (
                split_agent_result(
                    issue_agent_result
                )
            )

            top_segment = (
                extract_top_segment(
                    issue_sections[
                        "cause"
                    ]
                )
            )

            segment_block = (
                extract_segment_block(
                    issue_sections[
                        "cause"
                    ],
                    top_segment,
                )
            )

            contribution = (
                extract_value(
                    segment_block,
                    "Revenue Contribution",
                )
            )

            session_change = (
                extract_value(
                    segment_block,
                    "Sessions 변화",
                )
            )

            cvr_change = (
                extract_value(
                    segment_block,
                    "Purchase CVR 변화",
                )
            )

            issue_table = Table(
                [
                    [
                        Paragraph(
                            "주요 영향 구간",
                            styles[
                                "table_header"
                            ],
                        ),

                        Paragraph(
                            "매출 변화 기여",
                            styles[
                                "table_header"
                            ],
                        ),

                        Paragraph(
                            "세션 변화",
                            styles[
                                "table_header"
                            ],
                        ),

                        Paragraph(
                            "구매 전환율 변화",
                            styles[
                                "table_header"
                            ],
                        ),
                    ],

                    [
                        Paragraph(
                            safe_text(
                                top_segment
                                or "-"
                            ),
                            styles[
                                "table_body"
                            ],
                        ),

                        Paragraph(
                            safe_text(
                                contribution
                            ),
                            styles[
                                "table_body"
                            ],
                        ),

                        Paragraph(
                            safe_text(
                                session_change
                            ),
                            styles[
                                "table_body"
                            ],
                        ),

                        Paragraph(
                            safe_text(
                                cvr_change
                            ),
                            styles[
                                "table_body"
                            ],
                        ),
                    ],
                ],
                colWidths=[
                    48 * mm,
                    39 * mm,
                    37 * mm,
                    40 * mm,
                ],
            )

            apply_standard_table_style(
                issue_table
            )

            story.append(
                issue_table
            )

            funnel_rows = (
                parse_funnel_rows(
                    issue_sections[
                        "funnel"
                    ]
                )
            )

            if funnel_rows:

                funnel_block = [

                    Paragraph(
                        "핵심 세그먼트 퍼널 변화",
                        styles[
                            "subheading"
                        ],
                    )
                ]

                funnel_data = [
                    [
                        Paragraph(
                            "퍼널 단계",
                            styles[
                                "table_header"
                            ],
                        ),

                        Paragraph(
                            "당일",
                            styles[
                                "table_header"
                            ],
                        ),

                        Paragraph(
                            "7일 평균 대비",
                            styles[
                                "table_header"
                            ],
                        ),
                    ]
                ]

                for row_data in funnel_rows:

                    funnel_data.append(
                        [
                            Paragraph(
                                safe_text(
                                    row_data[
                                        0
                                    ]
                                ),
                                styles[
                                    "table_body"
                                ],
                            ),

                            Paragraph(
                                safe_text(
                                    row_data[
                                        1
                                    ]
                                ),
                                styles[
                                    "table_body"
                                ],
                            ),

                            Paragraph(
                                safe_text(
                                    row_data[
                                        2
                                    ]
                                ),
                                styles[
                                    "table_body"
                                ],
                            ),
                        ]
                    )

                funnel_table = Table(
                    funnel_data,
                    colWidths=[
                        72 * mm,
                        43 * mm,
                        49 * mm,
                    ],
                    repeatRows=1,
                )

                apply_standard_table_style(
                    funnel_table
                )

                funnel_block.append(
                    funnel_table
                )

                story.append(
                    KeepTogether(
                        funnel_block
                    )
                )

            conclusion = (
                clean_markdown(
                    issue_sections[
                        "conclusion"
                    ]
                )
            )

            if conclusion:

                story.append(
                    Paragraph(
                        "분석 요약",
                        styles[
                            "subheading"
                        ],
                    )
                )

                story.append(
                    Paragraph(
                        safe_text(
                            conclusion
                        ),
                        styles[
                            "body"
                        ],
                    )
                )

        else:

            story.append(
                Paragraph(
                    (
                        "해당 날짜에는 이상 징후가 존재하지만 "
                        "저장된 AI 원인 분석 결과가 없습니다."
                    ),
                    styles[
                        "body"
                    ],
                )
            )

    else:

        story.append(
            Paragraph(
                (
                    "해당 기간에는 별도로 확인할 "
                    "주요 이상 발생일이 없습니다."
                ),
                styles[
                    "body"
                ],
            )
        )


    # ==================================================
    # 4. Weekly Data Quality
    # ==================================================

    story.append(
        Paragraph(
            "4. 주간 데이터 품질",
            styles[
                "heading"
            ],
        )
    )

    quality_table = Table(
        [
            [
                Paragraph(
                    "점검 항목",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "현재 상태",
                    styles[
                        "table_header"
                    ],
                ),

                Paragraph(
                    "판정",
                    styles[
                        "table_header"
                    ],
                ),
            ],

            [
                Paragraph(
                    "Revenue 유효일",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        f"{revenue_valid_days}"
                        f" / {total_days}일"
                    ),
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "충족"
                        if revenue_valid_days
                        == total_days
                        else "일부 제외"
                    ),
                    styles[
                        "table_body"
                    ],
                ),
            ],

            [
                Paragraph(
                    "이상 탐지 가능일",
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        f"{anomaly_ready_days}"
                        f" / {total_days}일"
                    ),
                    styles[
                        "table_body"
                    ],
                ),

                Paragraph(
                    (
                        "충족"
                        if anomaly_ready_days
                        == total_days
                        else "일부 제한"
                    ),
                    styles[
                        "table_body"
                    ],
                ),
            ],
        ],
        colWidths=[
            70 * mm,
            47 * mm,
            47 * mm,
        ],
    )

    apply_standard_table_style(
        quality_table
    )

    story.append(
        quality_table
    )


    # ==================================================
    # 5. Method
    # ==================================================

    story.append(
        Paragraph(
            "5. 분석 기준",
            styles[
                "heading"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Weekly Report는 선택한 기준일을 포함한 최근 7일을 "
                "분석 대상으로 사용합니다. "
                "주간 구매 전환율은 일별 전환율의 단순 평균이 아니라 "
                "각 날짜의 세션 수를 반영한 가중 값으로 집계합니다."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "일별 이상 탐지는 Daily Monitoring과 동일하게 "
                "|Z-score| ≥ 2.0과 "
                "|최근 7일 평균 대비 편차| ≥ 30%를 "
                "동시에 충족한 경우로 정의합니다."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "주간 주요 이슈는 해당 기간 중 anomaly_count가 "
                "가장 높은 날짜를 우선 대상으로 선정합니다."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    caution_table = Table(
        [
            [
                Paragraph(
                    (
                        "<b>분석 해석 시 유의사항</b><br/>"
                        "Weekly Report는 일별 KPI 이상 징후와 "
                        "기여도가 높은 주요 원인 후보를 요약합니다. "
                        "실제 프로모션, 제품 변경, 마케팅 활동 및 장애 여부는 "
                        "별도 비즈니스 정보를 함께 확인해야 합니다."
                    ),
                    styles[
                        "warning"
                    ],
                )
            ]
        ],
        colWidths=[
            164 * mm
        ],
    )

    caution_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F3F4F6"
                    ),
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#D1D5DB"
                    ),
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(
        caution_table
    )

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf_bytes = (
        buffer.getvalue()
    )

    buffer.close()

    return pdf_bytes