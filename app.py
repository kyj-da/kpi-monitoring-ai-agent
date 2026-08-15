import json
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from google.cloud import bigquery

from tools.bigquery_client import (
    get_bigquery_client,
    get_anomaly_by_date,
)

from tools.rca_tools import (
    analyze_device_rca,
    analyze_landing_page_type_rca,
    analyze_device_landing_rca,
    analyze_funnel_rca,
    clear_query_logs,
    get_query_logs,
)

from reports.report_generator import (
    create_daily_report_pdf,
    create_weekly_report_pdf,
)


# ==================================================
# Page
# ==================================================

st.set_page_config(
    page_title="KPI Monitoring AI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# CSS
# ==================================================

st.markdown(
    """
<style>

.block-container {
    max-width: 1650px;
    padding-top: 2.2rem;
    padding-bottom: 4rem;
}

h1 {
    font-size: 2rem !important;
    font-weight: 750 !important;
    letter-spacing: -0.03em;
}

.page-description {
    color: #9ca3af;
    font-size: 0.92rem;
    margin-top: -8px;
    margin-bottom: 24px;
}

.section-title {
    font-size: 1.18rem;
    font-weight: 700;
    margin-top: 12px;
    margin-bottom: 14px;
}

.section-description {
    font-size: 0.84rem;
    color: #9ca3af;
    margin-top: -8px;
    margin-bottom: 14px;
}

.top-filter-wrap {
    height: 18px;
}

.kpi-card {
    border: 1px solid rgba(128,128,128,0.27);
    border-radius: 12px;
    padding: 18px;
    min-height: 165px;
    background: rgba(255,255,255,0.025);
}

.kpi-label {
    font-size: 0.88rem;
    font-weight: 650;
    color: #d1d5db;
    margin-bottom: 9px;
}

.kpi-value {
    font-size: 1.9rem;
    font-weight: 750;
    margin-bottom: 9px;
}

.kpi-positive {
    color: #4ade80;
    font-size: 0.83rem;
    font-weight: 650;
}

.kpi-negative {
    color: #f87171;
    font-size: 0.83rem;
    font-weight: 650;
}

.kpi-neutral {
    color: #9ca3af;
    font-size: 0.83rem;
}

.kpi-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 18px;
}

.badge-normal {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 7px;
    font-size: 0.75rem;
    font-weight: 650;
    background-color: rgba(34,197,94,0.15);
    color: #4ade80;
}

.badge-anomaly {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 7px;
    font-size: 0.75rem;
    font-weight: 650;
    background-color: rgba(239,68,68,0.16);
    color: #f87171;
}

.badge-na {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 7px;
    font-size: 0.75rem;
    font-weight: 650;
    background-color: rgba(156,163,175,0.15);
    color: #9ca3af;
}

.anomaly-score {
    color: #9ca3af;
    font-size: 0.74rem;
}

.legend-row {
    display: flex;
    gap: 24px;
    align-items: center;
    font-size: 0.82rem;
    color: #9ca3af;
    margin-bottom: 8px;
}

.sidebar-title {
    font-size: 1.08rem;
    font-weight: 750;
}

.sidebar-subtitle {
    font-size: 0.76rem;
    color: #9ca3af;
    margin-bottom: 18px;
}

.source-card {
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 10px;
    padding: 14px;
    margin-top: 20px;
    font-size: 0.78rem;
}

.source-label {
    color: #9ca3af;
    margin-bottom: 3px;
}

.analysis-card {
    border: 1px solid rgba(128,128,128,0.27);
    border-radius: 12px;
    padding: 18px;
    min-height: 245px;
    background: rgba(255,255,255,0.025);
    height: 100%;
}

.analysis-card-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #d1d5db;
    margin-bottom: 14px;
}

.analysis-highlight {
    font-size: 1.25rem;
    font-weight: 750;
    margin-bottom: 14px;
}

.analysis-item {
    font-size: 0.84rem;
    margin-bottom: 9px;
    color: #d1d5db;
    line-height: 1.6;
}

.analysis-positive {
    color: #4ade80;
    font-weight: 650;
}

.analysis-negative {
    color: #f87171;
    font-weight: 650;
}

.analysis-neutral {
    color: #d1d5db;
    font-weight: 650;
}

.ai-summary-text {
    color: #d1d5db;
    font-size: 0.84rem;
    line-height: 1.75;
}

</style>
""",
    unsafe_allow_html=True,
)


# ==================================================
# BigQuery
# ==================================================

@st.cache_data(ttl=300)
def get_available_dates():

    client = (
        get_bigquery_client()
    )

    query = """
    SELECT DISTINCT
      date
    FROM `silken-setting-502904-m2.kpi_agent.kpi_anomaly_monitoring`
    ORDER BY date DESC
    """

    return (
        client
        .query(
            query
        )
        .to_dataframe()[
            "date"
        ]
        .tolist()
    )


@st.cache_data(ttl=300)
def get_daily_kpi(
    target_date
):

    client = (
        get_bigquery_client()
    )

    query = """
    SELECT *
    FROM `silken-setting-502904-m2.kpi_agent.kpi_anomaly_monitoring`
    WHERE date = @target_date
    """

    job_config = (
        bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "target_date",
                    "DATE",
                    target_date,
                )
            ]
        )
    )

    return (
        client
        .query(
            query,
            job_config=job_config,
        )
        .to_dataframe()
    )


@st.cache_data(ttl=300)
def get_kpi_trend(
    target_date,
    days=14,
):

    client = (
        get_bigquery_client()
    )

    query = """
    SELECT
      date,

      sessions,
      sessions_7d_avg,
      sessions_anomaly,

      view_to_cart_pct,
      view_to_cart_7d_avg,
      view_to_cart_anomaly,

      purchase_cvr_pct,
      purchase_cvr_7d_avg,
      purchase_cvr_anomaly,

      validated_revenue,
      revenue_7d_avg,
      revenue_anomaly,
      revenue_data_valid

    FROM `silken-setting-502904-m2.kpi_agent.kpi_anomaly_monitoring`

    WHERE date BETWEEN
      DATE_SUB(@target_date, INTERVAL @lookback DAY)
      AND @target_date

    ORDER BY date
    """

    job_config = (
        bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "target_date",
                    "DATE",
                    target_date,
                ),

                bigquery.ScalarQueryParameter(
                    "lookback",
                    "INT64",
                    days - 1,
                ),
            ]
        )
    )

    df = (
        client
        .query(
            query,
            job_config=job_config,
        )
        .to_dataframe()
    )

    df[
        "date"
    ] = pd.to_datetime(
        df[
            "date"
        ]
    )

    return df


@st.cache_data(ttl=300)
def get_quality_history(
    target_date,
    days=14,
):

    client = (
        get_bigquery_client()
    )

    query = """
    SELECT
      date,
      history_day_count,
      revenue_valid_day_count,
      revenue_data_valid,
      sessions,
      view_to_cart_pct,
      purchase_cvr_pct,
      validated_revenue,
      any_anomaly,
      anomaly_count

    FROM `silken-setting-502904-m2.kpi_agent.kpi_anomaly_monitoring`

    WHERE date BETWEEN
      DATE_SUB(@target_date, INTERVAL @lookback DAY)
      AND @target_date

    ORDER BY date DESC
    """

    job_config = (
        bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "target_date",
                    "DATE",
                    target_date,
                ),

                bigquery.ScalarQueryParameter(
                    "lookback",
                    "INT64",
                    days - 1,
                ),
            ]
        )
    )

    return (
        client
        .query(
            query,
            job_config=job_config,
        )
        .to_dataframe()
    )


@st.cache_data(ttl=300)
def get_weekly_kpi(
    target_date
):

    client = (
        get_bigquery_client()
    )

    query = """
    SELECT
      date,
      sessions,
      purchase_cvr_pct,
      view_to_cart_pct,
      validated_revenue,

      sessions_anomaly,
      sessions_zscore,

      view_to_cart_anomaly,
      view_to_cart_zscore,

      purchase_cvr_anomaly,
      purchase_cvr_zscore,

      revenue_anomaly,
      revenue_zscore,

      anomaly_count,
      any_anomaly,

      history_day_count,
      revenue_valid_day_count,
      revenue_data_valid

    FROM `silken-setting-502904-m2.kpi_agent.kpi_anomaly_monitoring`

    WHERE date BETWEEN
      DATE_SUB(@target_date, INTERVAL 6 DAY)
      AND @target_date

    ORDER BY date
    """

    job_config = (
        bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "target_date",
                    "DATE",
                    target_date,
                )
            ]
        )
    )

    df = (
        client
        .query(
            query,
            job_config=job_config,
        )
        .to_dataframe()
    )

    df[
        "date"
    ] = pd.to_datetime(
        df[
            "date"
        ]
    )

    return df


# ==================================================
# Query Log Reproduction
# ==================================================

@st.cache_data(ttl=3600)
def reproduce_query_logs(
    target_date: str
):

    anomaly_df = (
        get_anomaly_by_date(
            target_date
        )
    )

    if anomaly_df.empty:

        return {
            "has_data":
                False,

            "has_anomaly":
                False,

            "query_logs":
                [],

            "top_segment":
                None,
        }

    anomaly_row = (
        anomaly_df.iloc[
            0
        ]
    )

    if not bool(
        anomaly_row.get(
            "any_anomaly",
            False,
        )
    ):

        return {
            "has_data":
                True,

            "has_anomaly":
                False,

            "query_logs":
                [],

            "top_segment":
                None,
        }

    clear_query_logs()

    analyze_device_rca(
        target_date
    )

    analyze_landing_page_type_rca(
        target_date
    )

    segment_df = (
        analyze_device_landing_rca(
            target_date
        )
    )

    top_segment = None

    if not segment_df.empty:

        top_row = (
            segment_df.iloc[
                0
            ]
        )

        top_device = str(
            top_row[
                "device"
            ]
        )

        top_landing = str(
            top_row[
                "landing_page_type"
            ]
        )

        top_segment = {
            "device":
                top_device,

            "landing_page_type":
                top_landing,
        }

        analyze_funnel_rca(
            target_date=target_date,
            device=top_device,
            landing_page_type=top_landing,
        )

    return {
        "has_data":
            True,

        "has_anomaly":
            True,

        "query_logs":
            get_query_logs(),

        "top_segment":
            top_segment,
    }


# ==================================================
# Helper
# ==================================================

def is_missing(
    value
):

    return pd.isna(
        value
    )


def format_score(
    value
):

    if is_missing(
        value
    ):

        return "-"

    return (
        f"{float(value):.2f}"
    )


def get_status_html(
    is_anomaly,
    score,
    data_valid=True,
):

    if not data_valid:

        return (
            '<span class="badge-na">분석 제외</span>',
            "-",
        )

    if bool(
        is_anomaly
    ):

        direction = (
            "이상 상승"
            if (
                not is_missing(
                    score
                )
                and score > 0
            )
            else "이상 하락"
        )

        return (
            f'<span class="badge-anomaly">{direction}</span>',
            format_score(
                score
            ),
        )

    return (
        '<span class="badge-normal">정상</span>',
        format_score(
            score
        ),
    )


def get_delta_html(
    value
):

    if is_missing(
        value
    ):

        return (
            '<span class="kpi-neutral">'
            "최근 7일 평균 비교 불가"
            "</span>"
        )

    value = float(
        value
    )

    if value > 0:

        return (
            '<span class="kpi-positive">'
            f"▲ {value:.2f}%"
            "</span>"
        )

    if value < 0:

        return (
            '<span class="kpi-negative">'
            f"▼ {abs(value):.2f}%"
            "</span>"
        )

    return (
        '<span class="kpi-neutral">'
        "0.00%"
        "</span>"
    )


def render_kpi_card(
    label,
    value,
    deviation,
    anomaly,
    score,
    data_valid=True,
):

    status_html, score_text = (
        get_status_html(
            anomaly,
            score,
            data_valid,
        )
    )

    delta_html = (
        get_delta_html(
            deviation
        )
        if data_valid
        else (
            '<span class="kpi-neutral">'
            "데이터 품질 기준 미충족"
            "</span>"
        )
    )

    st.html(
        f"""
<div class="kpi-card">

<div class="kpi-label">
{label}
</div>

<div class="kpi-value">
{value}
</div>

<div>
{delta_html}
<span class="kpi-neutral">
&nbsp;vs 최근 7일 평균
</span>
</div>

<div class="kpi-bottom">

<div>
{status_html}
</div>

<div class="anomaly-score">
이상 점수 {score_text}
</div>

</div>

</div>
"""
    )


def make_trend_chart(
    df,
    metric_col,
    avg_col,
    anomaly_col,
    title,
    value_format=".2f",
):

    chart_df = (
        df[
            [
                "date",
                metric_col,
                avg_col,
                anomaly_col,
            ]
        ]
        .copy()
        .rename(
            columns={
                metric_col:
                    "actual",

                avg_col:
                    "baseline",

                anomaly_col:
                    "anomaly",
            }
        )
    )

    base = (
        alt.Chart(
            chart_df
        )
        .encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(
                    format="%m-%d",
                    labelAngle=0,
                    tickCount=5,
                ),
            )
        )
    )

    actual_line = (
        base
        .mark_line(
            strokeWidth=2
        )
        .encode(
            y=alt.Y(
                "actual:Q",
                title=None,
                scale=alt.Scale(
                    zero=False
                ),
            ),

            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="날짜",
                    format="%Y-%m-%d",
                ),

                alt.Tooltip(
                    "actual:Q",
                    title="실제 값",
                    format=value_format,
                ),
            ],
        )
    )

    baseline_line = (
        base
        .mark_line(
            strokeDash=[
                5,
                5,
            ],
            opacity=0.65,
        )
        .encode(
            y=alt.Y(
                "baseline:Q",
                title=None,
            )
        )
    )

    anomaly_point = (
        base
        .transform_filter(
            alt.datum.anomaly
            == True
        )
        .mark_circle(
            size=90
        )
        .encode(
            y="actual:Q",
            color=alt.value(
                "#ef4444"
            ),
        )
    )

    return (
        actual_line
        + baseline_line
        + anomaly_point
    ).properties(
        title=title,
        height=210,
    )


def get_latest_analysis_log(
    target_date: str
):

    log_dir = (
        Path(
            "logs"
        )
    )

    log_files = list(
        log_dir.glob(
            f"rca_{target_date}_*.json"
        )
    )

    if not log_files:

        return None

    latest_file = max(
        log_files,
        key=lambda path:
            path.stat().st_mtime,
    )

    with open(
        latest_file,
        "r",
        encoding="utf-8",
    ) as f:

        data = (
            json.load(
                f
            )
        )

    data[
        "_file_name"
    ] = latest_file.name

    return data


def split_agent_result(
    result: str
):

    section_mapping = {

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

    sections = {
        "anomaly": "",
        "cause": "",
        "funnel": "",
        "conclusion": "",
        "caution": "",
    }

    current_section = None

    for line in (
        result.splitlines()
    ):

        stripped = (
            line.strip()
        )

        matched = False

        for (
            title,
            key,
        ) in section_mapping.items():

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


def extract_top_segment(
    cause_text
):

    match = re.search(
        r"\*\*([A-Za-z]+)\s*×\s*([A-Za-z ]+)\*\*",
        cause_text,
    )

    if match:

        return (
            f"{match.group(1).strip()} × "
            f"{match.group(2).strip()}"
        )

    return (
        "주요 영향 구간 확인"
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

    escaped_segment = (
        re.escape(
            segment_name
        )
    )

    pattern = (
        rf"-\s*\*\*{escaped_segment}\*\*"
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


def extract_metric(
    text,
    keyword,
):

    if not text:

        return "-"

    pattern = (
        rf"{re.escape(keyword)}"
        rf".*?\*\*([+-]?[0-9,.]+%?p?)\*\*"
    )

    match = re.search(
        pattern,
        text,
        re.S | re.I,
    )

    if match:

        return match.group(
            1
        )

    return "-"


def extract_change_metric(
    text,
    metric_name,
):

    if not text:
        return "-"

    # 예:
    # Sessions: 1,224, 전주 7일 평균 대비 +31.23%
    # Purchase CVR: 2.94%, +2.00%p
    pattern = (
        rf"{re.escape(metric_name)}"
        rf".*?([+-][0-9,.]+%p?)"
    )

    match = re.search(
        pattern,
        text,
        re.S | re.I,
    )

    if match:
        return match.group(1)

    return "-"


def get_change_class(
    value
):

    value = str(
        value
        or ""
    ).strip()

    if value.startswith(
        "-"
    ):

        return (
            "analysis-negative"
        )

    if value.startswith(
        "+"
    ):

        return (
            "analysis-positive"
        )

    return (
        "analysis-neutral"
    )


def clean_markdown_text(
    text
):

    if not text:

        return ""

    text = re.sub(
        r"#{1,6}\s*",
        "",
        text,
    )

    text = (
        text
        .replace(
            "**",
            "",
        )
        .replace(
            "__",
            "",
        )
        .replace(
            "`",
            "",
        )
    )

    return (
        text.strip()
    )


def build_ai_summary(
    conclusion_text
):

    cleaned = (
        clean_markdown_text(
            conclusion_text
        )
    )

    if not cleaned:

        return (
            "상세 분석 결과에서 주요 원인 후보를 확인할 수 있습니다."
        )

    lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    ]

    summary = (
        " ".join(
            lines
        )
    )

    if len(
        summary
    ) > 380:

        summary = (
            summary[
                :380
            ].rstrip()
            + "..."
        )

    return summary


# ==================================================
# Sidebar
# ==================================================

with st.sidebar:

    st.markdown(
        """
<div class="sidebar-title">
📊 KPI Monitoring AI
</div>

<div class="sidebar-subtitle">
데이터 기반 지표 모니터링 및 원인 분석
</div>
""",
        unsafe_allow_html=True,
    )

    menu = st.radio(
        "메뉴",
        [
            "🏠 핵심 지표 모니터링",
            "📐 지표 정의 및 계산 기준",
            "🧾 분석 쿼리 기록",
            "🛡️ 데이터 품질",
            "📄 Daily Report",
            "📊 Weekly Report",
        ],
        index=0,
    )

    st.divider()

    st.html(
        """
<div class="source-card">

<div class="source-label">
원천 데이터
</div>
<div>GA4 E-commerce Sample Dataset</div>

<br>

<div class="source-label">
Dataset
</div>
<div>ga4_obfuscated_sample_ecommerce</div>

<br>

<div class="source-label">
기간
</div>
<div>2020.11.01 ~ 2021.01.31</div>

</div>
"""
    )


dates = (
    get_available_dates()
)


# ==================================================
# 1. Monitoring
# ==================================================

if menu == "🏠 핵심 지표 모니터링":

    header1, header2 = (
        st.columns(
            [
                2.6,
                1,
            ]
        )
    )

    with header1:

        st.title(
            "핵심 지표 모니터링"
        )

        st.markdown(
            """
<div class="page-description">
핵심 지표의 최근 흐름과 이상 징후를 확인하고,
필요 시 AI를 통해 주요 원인 후보를 분석합니다.
</div>
""",
            unsafe_allow_html=True,
        )

    with header2:

        st.markdown(
            '<div class="top-filter-wrap"></div>',
            unsafe_allow_html=True,
        )

        c1, c2 = (
            st.columns(
                2
            )
        )

        with c1:

            selected_date = (
                st.selectbox(
                    "분석 기준일",
                    dates,
                    index=0,
                )
            )

        with c2:

            st.selectbox(
                "비교 기준",
                [
                    "최근 7일 평균"
                ],
            )

    daily_df = (
        get_daily_kpi(
            selected_date
        )
    )

    if daily_df.empty:

        st.warning(
            "선택한 날짜의 데이터가 없습니다."
        )

        st.stop()

    row = (
        daily_df.iloc[
            0
        ]
    )

    st.divider()

    st.markdown(
        '<div class="section-title">핵심 지표 요약</div>',
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = (
        st.columns(
            4
        )
    )

    with k1:

        render_kpi_card(
            "👥 세션 수",
            f"{int(row['sessions']):,}",
            row[
                "sessions_avg_deviation_pct"
            ],
            row[
                "sessions_anomaly"
            ],
            row[
                "sessions_zscore"
            ],
        )

    with k2:

        render_kpi_card(
            "🛒 조회 → 장바구니 전환율",
            f"{row['view_to_cart_pct']:.2f}%",
            row[
                "view_to_cart_avg_deviation_pct"
            ],
            row[
                "view_to_cart_anomaly"
            ],
            row[
                "view_to_cart_zscore"
            ],
        )

    with k3:

        render_kpi_card(
            "📈 구매 전환율",
            f"{row['purchase_cvr_pct']:.2f}%",
            row[
                "purchase_cvr_avg_deviation_pct"
            ],
            row[
                "purchase_cvr_anomaly"
            ],
            row[
                "purchase_cvr_zscore"
            ],
        )

    with k4:

        revenue_valid = bool(
            row[
                "revenue_data_valid"
            ]
        )

        render_kpi_card(
            "💰 유효 매출",
            (
                f"{row['validated_revenue']:,.0f}"
                if revenue_valid
                else "N/A"
            ),
            row[
                "revenue_avg_deviation_pct"
            ],
            row[
                "revenue_anomaly"
            ],
            row[
                "revenue_zscore"
            ],
            revenue_valid,
        )

    st.write("")

    st.markdown(
        '<div class="section-title">지표 추이</div>',
        unsafe_allow_html=True,
    )

    trend_df = (
        get_kpi_trend(
            selected_date
        )
    )

    chart1, chart2, chart3, chart4 = (
        st.columns(
            4
        )
    )

    with chart1:

        st.altair_chart(
            make_trend_chart(
                trend_df,
                "sessions",
                "sessions_7d_avg",
                "sessions_anomaly",
                "세션 수",
                ",.0f",
            ),
            width="stretch",
        )

    with chart2:

        st.altair_chart(
            make_trend_chart(
                trend_df,
                "view_to_cart_pct",
                "view_to_cart_7d_avg",
                "view_to_cart_anomaly",
                "조회 → 장바구니",
            ),
            width="stretch",
        )

    with chart3:

        st.altair_chart(
            make_trend_chart(
                trend_df,
                "purchase_cvr_pct",
                "purchase_cvr_7d_avg",
                "purchase_cvr_anomaly",
                "구매 전환율",
            ),
            width="stretch",
        )

    with chart4:

        revenue_df = (
            trend_df[
                trend_df[
                    "revenue_data_valid"
                ] == True
            ]
        )

        st.altair_chart(
            make_trend_chart(
                revenue_df,
                "validated_revenue",
                "revenue_7d_avg",
                "revenue_anomaly",
                "유효 매출",
                ",.0f",
            ),
            width="stretch",
        )

    st.divider()

    st.markdown(
        '<div class="section-title">이상 징후</div>',
        unsafe_allow_html=True,
    )

    if bool(
        row[
            "any_anomaly"
        ]
    ):

        st.error(
            f"⚠️ {selected_date} 기준 "
            f"{int(row['anomaly_count'])}개 KPI에서 이상 징후가 감지되었습니다."
        )

        if st.button(
            "🤖 AI로 원인 분석",
            type="primary",
            width="stretch",
        ):

            from agent.agent import (
                run_kpi_agent
            )

            with st.spinner(
                "AI Agent가 원인을 분석하고 있습니다..."
            ):

                result = (
                    run_kpi_agent(
                        str(
                            selected_date
                        )
                    )
                )

                st.session_state[
                    "rca_result"
                ] = result

                st.session_state[
                    "rca_date"
                ] = str(
                    selected_date
                )

    else:

        st.success(
            "✅ 이상 징후가 감지되지 않았습니다."
        )

    if (
        st.session_state.get(
            "rca_date"
        )
        == str(
            selected_date
        )
    ):

        result = (
            st.session_state[
                "rca_result"
            ]
        )

        sections = (
            split_agent_result(
                result
            )
        )

        st.divider()

        st.markdown(
            '<div class="section-title">원인 분석 요약</div>',
            unsafe_allow_html=True,
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

        contribution = (
            extract_metric(
                segment_block,
                "Revenue Contribution",
            )
        )

        session_change = (
            extract_change_metric(
                segment_block,
                "Sessions",
            )
        )

        cvr_change = (
            extract_change_metric(
                segment_block,
                "Purchase CVR",
            )
        )

        a1, a2, a3 = (
            st.columns(
                3
            )
        )

        with a1:

            st.metric(
                "주요 영향 구간",
                top_segment,
            )

        with a2:

            st.metric(
                "매출 변화 기여",
                contribution,
            )

        with a3:

            st.metric(
                "구매 전환율 변화",
                cvr_change,
            )

        with st.expander(
            "🔎 상세 분석 결과 보기"
        ):

            st.markdown(
                result
            )


# ==================================================
# 2. Metric Definition
# ==================================================

elif menu == "📐 지표 정의 및 계산 기준":

    st.title(
        "지표 정의 및 계산 기준"
    )

    st.markdown(
        """
<div class="page-description">
모니터링에 사용되는 핵심 지표의 정의와 SQL 계산 기준을 확인합니다.
</div>
""",
        unsafe_allow_html=True,
    )

    t1, t2, t3, t4 = (
        st.tabs(
            [
                "세션 수",
                "조회 → 장바구니",
                "구매 전환율",
                "유효 매출",
            ]
        )
    )

    with t1:

        st.markdown(
            """
### 세션 수

`session_start`가 존재하는
`user_pseudo_id + ga_session_id` 고유 조합을 하나의 세션으로 정의합니다.
"""
        )

        st.code(
            """
CONCAT(
    user_pseudo_id,
    '-',
    CAST(ga_session_id AS STRING)
) AS session_key
            """,
            language="sql",
        )

    with t2:

        st.code(
            """
SAFE_DIVIDE(
    SUM(add_to_cart_flag),
    SUM(view_item_flag)
) * 100 AS view_to_cart_pct
            """,
            language="sql",
        )

    with t3:

        st.code(
            """
SAFE_DIVIDE(
    SUM(purchase_flag),
    COUNT(*)
) * 100 AS purchase_cvr_pct
            """,
            language="sql",
        )

    with t4:

        st.code(
            """
SUM(validated_revenue)
AS validated_revenue
            """,
            language="sql",
        )

        st.markdown(
            "`Transaction Coverage ≥ 80%`인 경우에만 Revenue 이상 탐지에 사용합니다."
        )


# ==================================================
# 3. Query Logs
# ==================================================

elif menu == "🧾 분석 쿼리 기록":

    st.title(
        "분석 쿼리 기록"
    )

    selected_log_date = (
        st.selectbox(
            "분석 기준일",
            dates,
        )
    )

    saved_log = (
        get_latest_analysis_log(
            str(
                selected_log_date
            )
        )
    )

    query_logs = []

    if saved_log:

        query_logs = (
            saved_log.get(
                "query_logs",
                [],
            )
        )

    if not query_logs:

        with st.spinner(
            "선택 날짜 기준 분석 SQL을 재현하고 있습니다..."
        ):

            reproduced = (
                reproduce_query_logs(
                    str(
                        selected_log_date
                    )
                )
            )

        if not reproduced[
            "has_anomaly"
        ]:

            st.success(
                "이 날짜에는 이상 징후가 없어 RCA 쿼리를 실행하지 않습니다."
            )

            st.stop()

        query_logs = (
            reproduced[
                "query_logs"
            ]
        )

    st.metric(
        "실행 쿼리",
        f"{len(query_logs)}개",
    )

    for (
        index,
        log,
    ) in enumerate(
        query_logs,
        1,
    ):

        with st.expander(
            f"{index}. {log.get('display_name', log.get('tool'))}"
        ):

            st.markdown(
                "**분석 조건**"
            )

            st.json(
                log.get(
                    "arguments",
                    {},
                )
            )

            st.markdown(
                "**BigQuery Job ID**"
            )

            st.code(
                log.get(
                    "query_job_id",
                    "-"
                )
            )

            st.markdown(
                "**실행 SQL**"
            )

            st.code(
                log.get(
                    "sql",
                    "",
                ),
                language="sql",
            )


# ==================================================
# 4. Data Quality
# ==================================================

elif menu == "🛡️ 데이터 품질":

    st.title(
        "데이터 품질"
    )

    quality_date = (
        st.selectbox(
            "확인 기준일",
            dates,
        )
    )

    quality_df = (
        get_daily_kpi(
            quality_date
        )
    )

    if quality_df.empty:

        st.stop()

    row = (
        quality_df.iloc[
            0
        ]
    )

    q1, q2, q3, q4 = (
        st.columns(
            4
        )
    )

    with q1:

        st.metric(
            "기준 데이터 일수",
            f"{int(row['history_day_count'])}일",
        )

    with q2:

        st.metric(
            "Revenue 유효 기준 일수",
            f"{int(row['revenue_valid_day_count'])}일",
        )

    with q3:

        st.metric(
            "Revenue 상태",
            (
                "유효"
                if bool(
                    row[
                        "revenue_data_valid"
                    ]
                )
                else "분석 제외"
            ),
        )

    with q4:

        st.metric(
            "이상 탐지",
            (
                "가능"
                if int(
                    row[
                        "history_day_count"
                    ]
                ) >= 7
                else "기준 부족"
            ),
        )

    st.divider()

    history_df = (
        get_quality_history(
            quality_date
        )
    )

    history_df[
        "date"
    ] = pd.to_datetime(
        history_df[
            "date"
        ]
    ).dt.strftime(
        "%Y-%m-%d"
    )

    st.dataframe(
        history_df[
            [
                "date",
                "history_day_count",
                "revenue_valid_day_count",
                "revenue_data_valid",
            ]
        ].rename(
            columns={
                "date":
                    "날짜",

                "history_day_count":
                    "기준 데이터 일수",

                "revenue_valid_day_count":
                    "Revenue 유효 일수",

                "revenue_data_valid":
                    "Revenue 유효 여부",
            }
        ),
        width="stretch",
        hide_index=True,
    )


# ==================================================
# 5. Daily Report
# ==================================================

elif menu == "📄 Daily Report":

    st.title(
        "Daily Report"
    )

    st.markdown(
        """
<div class="page-description">
선택한 날짜의 KPI, 이상 징후, AI 원인 분석 및 데이터 품질을 PDF로 생성합니다.
</div>
""",
        unsafe_allow_html=True,
    )

    report_date = (
        st.selectbox(
            "리포트 기준일",
            dates,
        )
    )

    report_df = (
        get_daily_kpi(
            report_date
        )
    )

    if report_df.empty:

        st.stop()

    report_row = (
        report_df.iloc[
            0
        ]
    )

    report_log = (
        get_latest_analysis_log(
            str(
                report_date
            )
        )
    )

    agent_result = (
        report_log.get(
            "final_result"
        )
        if report_log
        else None
    )

    c1, c2, c3 = (
        st.columns(
            3
        )
    )

    with c1:

        st.metric(
            "리포트 기준일",
            str(
                report_date
            ),
        )

    with c2:

        st.metric(
            "이상 지표",
            f"{int(report_row['anomaly_count'])}개",
        )

    with c3:

        st.metric(
            "AI 원인 분석",
            (
                "분석 완료"
                if agent_result
                else "미실행"
            ),
        )

    st.divider()

    try:

        pdf_bytes = (
            create_daily_report_pdf(
                target_date=str(
                    report_date
                ),
                daily_row=report_row,
                agent_result=agent_result,
            )
        )

        st.download_button(
            "📥 Daily Report PDF 다운로드",
            data=pdf_bytes,
            file_name=(
                f"kpi_daily_report_"
                f"{report_date}.pdf"
            ),
            mime="application/pdf",
            type="primary",
            width="stretch",
        )

    except Exception as e:

        st.error(
            "PDF 생성 중 오류가 발생했습니다."
        )

        st.code(
            str(
                e
            )
        )


# ==================================================
# 6. Weekly Report
# ==================================================

elif menu == "📊 Weekly Report":

    st.title(
        "Weekly Report"
    )

    st.markdown(
        """
<div class="page-description">
선택한 기준일까지 최근 7일의 KPI 흐름, 이상 징후 및 주요 이슈를 요약합니다.
</div>
""",
        unsafe_allow_html=True,
    )

    weekly_date = (
        st.selectbox(
            "주간 기준일",
            dates,
        )
    )

    weekly_df = (
        get_weekly_kpi(
            weekly_date
        )
    )

    if weekly_df.empty:

        st.stop()

    start_date = (
        weekly_df[
            "date"
        ]
        .min()
        .strftime(
            "%Y-%m-%d"
        )
    )

    end_date = (
        weekly_df[
            "date"
        ]
        .max()
        .strftime(
            "%Y-%m-%d"
        )
    )

    st.info(
        f"📅 분석 기간: **{start_date} ~ {end_date}**"
    )

    total_sessions = int(
        weekly_df[
            "sessions"
        ].sum()
    )

    # 일별 CVR 단순 평균이 아니라
    # 세션 수를 반영한 주간 CVR
    estimated_purchase_sessions = (
        weekly_df[
            "sessions"
        ]
        * weekly_df[
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
        weekly_df[
            weekly_df[
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

    anomaly_days = int(
        weekly_df[
            "any_anomaly"
        ].sum()
    )

    st.markdown(
        '<div class="section-title">주간 KPI 요약</div>',
        unsafe_allow_html=True,
    )

    w1, w2, w3, w4 = (
        st.columns(
            4
        )
    )

    with w1:

        st.metric(
            "총 세션",
            f"{total_sessions:,}",
        )

    with w2:

        st.metric(
            "주간 구매 전환율",
            f"{weekly_purchase_cvr:.2f}%",
        )

    with w3:

        st.metric(
            "총 유효 매출",
            f"{total_revenue:,.0f}",
        )

    with w4:

        st.metric(
            "이상 발생일",
            f"{anomaly_days}일",
        )

    st.divider()

    st.markdown(
        '<div class="section-title">주간 KPI 추이</div>',
        unsafe_allow_html=True,
    )

    t1, t2, t3 = (
        st.columns(
            3
        )
    )

    with t1:

        st.line_chart(
            weekly_df.set_index(
                "date"
            )[
                "sessions"
            ]
        )

    with t2:

        st.line_chart(
            weekly_df.set_index(
                "date"
            )[
                "purchase_cvr_pct"
            ]
        )

    with t3:

        st.line_chart(
            valid_revenue_df.set_index(
                "date"
            )[
                "validated_revenue"
            ]
        )

    st.divider()

    st.markdown(
        '<div class="section-title">주간 이상 징후</div>',
        unsafe_allow_html=True,
    )

    anomaly_rows = []

    for _, row in (
        weekly_df.iterrows()
    ):

        date_text = (
            row[
                "date"
            ].strftime(
                "%Y-%m-%d"
            )
        )

        configs = [

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

        for (
            name,
            anomaly_col,
            score_col,
        ) in configs:

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
                    {
                        "날짜":
                            date_text,

                        "지표":
                            name,

                        "상태":
                            (
                                "이상 상승"
                                if score > 0
                                else "이상 하락"
                            ),

                        "이상 점수":
                            round(
                                score,
                                2,
                            ),
                    }
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
                {
                    "날짜":
                        date_text,

                    "지표":
                        "유효 매출",

                    "상태":
                        (
                            "이상 상승"
                            if score > 0
                            else "이상 하락"
                        ),

                    "이상 점수":
                        round(
                            score,
                            2,
                        ),
                }
            )

    if anomaly_rows:

        st.dataframe(
            pd.DataFrame(
                anomaly_rows
            ),
            width="stretch",
            hide_index=True,
        )

    else:

        st.success(
            "✅ 주간 내 이상 징후가 없습니다."
        )

    anomaly_day_df = (
        weekly_df[
            weekly_df[
                "any_anomaly"
            ] == True
        ]
        .sort_values(
            [
                "anomaly_count",
                "date",
            ],
            ascending=[
                False,
                False,
            ],
        )
    )

    st.write("")

    st.markdown(
        '<div class="section-title">주요 이슈</div>',
        unsafe_allow_html=True,
    )

    issue_date = None
    issue_agent_result = None

    if not anomaly_day_df.empty:

        issue_row = (
            anomaly_day_df.iloc[
                0
            ]
        )

        issue_date = (
            issue_row[
                "date"
            ].strftime(
                "%Y-%m-%d"
            )
        )

        issue_log = (
            get_latest_analysis_log(
                issue_date
            )
        )

        issue_agent_result = (
            issue_log.get(
                "final_result"
            )
            if issue_log
            else None
        )

        i1, i2, i3 = (
            st.columns(
                3
            )
        )

        with i1:

            st.metric(
                "주요 이상 발생일",
                issue_date,
            )

        with i2:

            st.metric(
                "이상 지표",
                f"{int(issue_row['anomaly_count'])}개",
            )

        with i3:

            st.metric(
                "AI 원인 분석",
                (
                    "완료"
                    if issue_agent_result
                    else "미실행"
                ),
            )

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

            st.info(
                f"**주요 영향 구간:** {issue_top_segment}"
            )

            st.markdown(
                build_ai_summary(
                    issue_sections[
                        "conclusion"
                    ]
                )
            )

    else:

        st.info(
            "주간 내 주요 이상 발생일이 없습니다."
        )

    st.divider()

    st.markdown(
        '<div class="section-title">주간 데이터 품질</div>',
        unsafe_allow_html=True,
    )

    revenue_valid_count = int(
        weekly_df[
            "revenue_data_valid"
        ].sum()
    )

    anomaly_ready_count = int(
        (
            weekly_df[
                "history_day_count"
            ] >= 7
        ).sum()
    )

    q1, q2 = (
        st.columns(
            2
        )
    )

    with q1:

        st.metric(
            "Revenue 유효일",
            (
                f"{revenue_valid_count} / "
                f"{len(weekly_df)}일"
            ),
        )

    with q2:

        st.metric(
            "이상 탐지 가능일",
            (
                f"{anomaly_ready_count} / "
                f"{len(weekly_df)}일"
            ),
        )

    st.divider()

    st.markdown(
        '<div class="section-title">Weekly Report PDF</div>',
        unsafe_allow_html=True,
    )

    try:

        weekly_pdf_bytes = (
            create_weekly_report_pdf(
                weekly_df=weekly_df,
                start_date=start_date,
                end_date=end_date,
                issue_date=issue_date,
                issue_agent_result=issue_agent_result,
            )
        )

        st.download_button(
            "📥 Weekly Report PDF 다운로드",
            data=weekly_pdf_bytes,
            file_name=(
                f"kpi_weekly_report_"
                f"{start_date}_"
                f"{end_date}.pdf"
            ),
            mime="application/pdf",
            type="primary",
            width="stretch",
        )

    except Exception as e:

        st.error(
            "Weekly PDF 생성 중 오류가 발생했습니다."
        )

        st.code(
            str(
                e
            )
        )