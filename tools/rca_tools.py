from datetime import datetime

from google.cloud import bigquery

from tools.bigquery_client import get_bigquery_client


# ==================================================
# Query Log
# ==================================================

_QUERY_LOGS = []


def clear_query_logs():
    """
    현재 프로세스에 저장된 RCA Query Log를 초기화합니다.
    새로운 Agent 분석을 시작할 때 호출합니다.
    """

    _QUERY_LOGS.clear()


def get_query_logs():
    """
    현재까지 실행된 RCA Query Log를 반환합니다.
    """

    return list(_QUERY_LOGS)


def execute_logged_query(
    tool_name: str,
    display_name: str,
    query: str,
    job_config: bigquery.QueryJobConfig,
    arguments: dict
):
    """
    BigQuery SQL을 실행하고,
    실행 정보를 Query Log에 기록합니다.

    기록 항목
    - Tool 이름
    - 분석 이름
    - 실행 파라미터
    - 실제 SQL
    - BigQuery Query Job ID
    - 실행 시각
    - 반환 행 수
    - 처리 데이터 크기
    """

    client = get_bigquery_client()

    executed_at = (
        datetime
        .now()
        .astimezone()
        .isoformat(timespec="seconds")
    )

    query_job = client.query(
        query,
        job_config=job_config
    )

    result = query_job.to_dataframe()

    query_log = {
        "tool": tool_name,
        "display_name": display_name,
        "arguments": arguments,
        "sql": query.strip(),
        "query_job_id": query_job.job_id,
        "executed_at": executed_at,
        "row_count": len(result),
        "total_bytes_processed": (
            query_job.total_bytes_processed
            if query_job.total_bytes_processed
            is not None
            else 0
        )
    }

    _QUERY_LOGS.append(
        query_log
    )

    return result


# ==================================================
# Device RCA
# ==================================================

def analyze_device_rca(target_date: str):
    """
    특정 날짜의 Device별 RCA 결과를 조회합니다.
    target_date 기준 직전 7일 평균과 비교합니다.
    """

    query = """
    WITH daily_device AS (
      SELECT
        date,
        device,

        COUNT(*) AS sessions,

        SUM(purchase_flag) AS purchase_sessions,

        SUM(validated_orders) AS validated_orders,

        SUM(validated_revenue) AS validated_revenue,

        SAFE_DIVIDE(
          SUM(purchase_flag),
          COUNT(*)
        ) * 100 AS purchase_cvr_pct

      FROM `silken-setting-502904-m2.kpi_agent.session_kpi_base`

      WHERE date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                     AND @target_date

      GROUP BY
        date,
        device
    ),

    baseline AS (
      SELECT
        device,

        AVG(sessions) AS sessions_7d_avg,

        AVG(purchase_cvr_pct)
          AS purchase_cvr_7d_avg,

        AVG(validated_revenue)
          AS revenue_7d_avg

      FROM daily_device

      WHERE date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                     AND DATE_SUB(@target_date, INTERVAL 1 DAY)

      GROUP BY device
    ),

    target AS (
      SELECT *
      FROM daily_device
      WHERE date = @target_date
    ),

    comparison AS (
      SELECT
        t.device,

        t.sessions,
        b.sessions_7d_avg,

        SAFE_DIVIDE(
          t.sessions - b.sessions_7d_avg,
          b.sessions_7d_avg
        ) * 100 AS sessions_change_pct,

        t.purchase_cvr_pct,
        b.purchase_cvr_7d_avg,

        t.purchase_cvr_pct
          - b.purchase_cvr_7d_avg
          AS purchase_cvr_change_pp,

        t.validated_revenue,
        b.revenue_7d_avg,

        SAFE_DIVIDE(
          t.validated_revenue - b.revenue_7d_avg,
          b.revenue_7d_avg
        ) * 100 AS revenue_change_pct,

        t.validated_revenue
          - b.revenue_7d_avg
          AS revenue_increment

      FROM target t

      LEFT JOIN baseline b
        ON t.device = b.device
    ),

    contribution AS (
      SELECT
        *,

        SUM(revenue_increment)
          OVER ()
          AS total_revenue_increment

      FROM comparison
    )

    SELECT
      device,

      sessions,

      ROUND(
        sessions_7d_avg,
        2
      ) AS sessions_7d_avg,

      ROUND(
        sessions_change_pct,
        2
      ) AS sessions_change_pct,

      ROUND(
        purchase_cvr_pct,
        2
      ) AS purchase_cvr_pct,

      ROUND(
        purchase_cvr_7d_avg,
        2
      ) AS purchase_cvr_7d_avg,

      ROUND(
        purchase_cvr_change_pp,
        2
      ) AS purchase_cvr_change_pp,

      validated_revenue,

      ROUND(
        revenue_7d_avg,
        2
      ) AS revenue_7d_avg,

      ROUND(
        revenue_change_pct,
        2
      ) AS revenue_change_pct,

      ROUND(
        revenue_increment,
        2
      ) AS revenue_increment,

      ROUND(
        SAFE_DIVIDE(
          revenue_increment,
          total_revenue_increment
        ) * 100,
        2
      ) AS revenue_contribution_pct

    FROM contribution

    ORDER BY
      revenue_increment DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "target_date",
                "DATE",
                target_date
            )
        ]
    )

    return execute_logged_query(
        tool_name="analyze_device_rca",
        display_name="Device별 영향 분석",
        query=query,
        job_config=job_config,
        arguments={
            "target_date": target_date
        }
    )


# ==================================================
# Landing Page Type RCA
# ==================================================

def analyze_landing_page_type_rca(
    target_date: str
):
    """
    특정 날짜의 Landing Page Type별 RCA 결과를 조회합니다.
    target_date 기준 직전 7일 평균과 비교합니다.
    """

    query = """
    WITH daily_landing AS (
      SELECT
        date,
        landing_page_type,

        COUNT(*) AS sessions,

        SUM(purchase_flag) AS purchase_sessions,

        SUM(validated_revenue) AS validated_revenue,

        SAFE_DIVIDE(
          SUM(purchase_flag),
          COUNT(*)
        ) * 100 AS purchase_cvr_pct

      FROM `silken-setting-502904-m2.kpi_agent.session_kpi_base`

      WHERE date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                     AND @target_date

      GROUP BY
        date,
        landing_page_type
    ),

    baseline AS (
      SELECT
        landing_page_type,

        AVG(sessions)
          AS sessions_7d_avg,

        AVG(purchase_cvr_pct)
          AS purchase_cvr_7d_avg,

        AVG(validated_revenue)
          AS revenue_7d_avg

      FROM daily_landing

      WHERE date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                     AND DATE_SUB(@target_date, INTERVAL 1 DAY)

      GROUP BY landing_page_type
    ),

    target AS (
      SELECT *
      FROM daily_landing
      WHERE date = @target_date
    ),

    comparison AS (
      SELECT
        t.landing_page_type,

        t.sessions,
        b.sessions_7d_avg,

        SAFE_DIVIDE(
          t.sessions - b.sessions_7d_avg,
          b.sessions_7d_avg
        ) * 100 AS sessions_change_pct,

        t.purchase_cvr_pct,
        b.purchase_cvr_7d_avg,

        t.purchase_cvr_pct
          - b.purchase_cvr_7d_avg
          AS purchase_cvr_change_pp,

        t.validated_revenue,
        b.revenue_7d_avg,

        SAFE_DIVIDE(
          t.validated_revenue - b.revenue_7d_avg,
          b.revenue_7d_avg
        ) * 100 AS revenue_change_pct,

        t.validated_revenue
          - b.revenue_7d_avg
          AS revenue_increment

      FROM target t

      LEFT JOIN baseline b
        ON t.landing_page_type = b.landing_page_type
    ),

    contribution AS (
      SELECT
        *,

        SUM(revenue_increment)
          OVER ()
          AS total_revenue_increment

      FROM comparison
    )

    SELECT
      landing_page_type,

      sessions,

      ROUND(
        sessions_7d_avg,
        2
      ) AS sessions_7d_avg,

      ROUND(
        sessions_change_pct,
        2
      ) AS sessions_change_pct,

      ROUND(
        purchase_cvr_pct,
        2
      ) AS purchase_cvr_pct,

      ROUND(
        purchase_cvr_7d_avg,
        2
      ) AS purchase_cvr_7d_avg,

      ROUND(
        purchase_cvr_change_pp,
        2
      ) AS purchase_cvr_change_pp,

      validated_revenue,

      ROUND(
        revenue_7d_avg,
        2
      ) AS revenue_7d_avg,

      ROUND(
        revenue_change_pct,
        2
      ) AS revenue_change_pct,

      ROUND(
        revenue_increment,
        2
      ) AS revenue_increment,

      ROUND(
        SAFE_DIVIDE(
          revenue_increment,
          total_revenue_increment
        ) * 100,
        2
      ) AS revenue_contribution_pct

    FROM contribution

    ORDER BY
      revenue_increment DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "target_date",
                "DATE",
                target_date
            )
        ]
    )

    return execute_logged_query(
        tool_name="analyze_landing_page_type_rca",
        display_name="Landing Page Type별 영향 분석",
        query=query,
        job_config=job_config,
        arguments={
            "target_date": target_date
        }
    )


# ==================================================
# Device × Landing Page RCA
# ==================================================

def analyze_device_landing_rca(
    target_date: str
):
    """
    특정 날짜의 Device × Landing Page Type 조합별
    RCA 결과를 조회합니다.

    target_date 기준 직전 7일 평균과 비교합니다.
    """

    query = """
    WITH daily_segment AS (
      SELECT
        date,
        device,
        landing_page_type,

        COUNT(*) AS sessions,

        SUM(purchase_flag) AS purchase_sessions,

        SUM(validated_revenue) AS validated_revenue,

        SAFE_DIVIDE(
          SUM(purchase_flag),
          COUNT(*)
        ) * 100 AS purchase_cvr_pct

      FROM `silken-setting-502904-m2.kpi_agent.session_kpi_base`

      WHERE date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                     AND @target_date

      GROUP BY
        date,
        device,
        landing_page_type
    ),

    baseline AS (
      SELECT
        device,
        landing_page_type,

        AVG(sessions)
          AS sessions_7d_avg,

        AVG(purchase_cvr_pct)
          AS purchase_cvr_7d_avg,

        AVG(validated_revenue)
          AS revenue_7d_avg

      FROM daily_segment

      WHERE date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                     AND DATE_SUB(@target_date, INTERVAL 1 DAY)

      GROUP BY
        device,
        landing_page_type
    ),

    target AS (
      SELECT *
      FROM daily_segment
      WHERE date = @target_date
    ),

    comparison AS (
      SELECT
        t.device,
        t.landing_page_type,

        t.sessions,
        b.sessions_7d_avg,

        SAFE_DIVIDE(
          t.sessions - b.sessions_7d_avg,
          b.sessions_7d_avg
        ) * 100 AS sessions_change_pct,

        t.purchase_cvr_pct,
        b.purchase_cvr_7d_avg,

        t.purchase_cvr_pct
          - b.purchase_cvr_7d_avg
          AS purchase_cvr_change_pp,

        t.validated_revenue,
        b.revenue_7d_avg,

        SAFE_DIVIDE(
          t.validated_revenue - b.revenue_7d_avg,
          b.revenue_7d_avg
        ) * 100 AS revenue_change_pct,

        t.validated_revenue
          - b.revenue_7d_avg
          AS revenue_increment

      FROM target t

      LEFT JOIN baseline b
        ON t.device = b.device
       AND t.landing_page_type = b.landing_page_type
    ),

    contribution AS (
      SELECT
        *,

        SUM(revenue_increment)
          OVER ()
          AS total_revenue_increment

      FROM comparison
    )

    SELECT
      device,
      landing_page_type,

      sessions,

      ROUND(
        sessions_7d_avg,
        2
      ) AS sessions_7d_avg,

      ROUND(
        sessions_change_pct,
        2
      ) AS sessions_change_pct,

      ROUND(
        purchase_cvr_pct,
        2
      ) AS purchase_cvr_pct,

      ROUND(
        purchase_cvr_7d_avg,
        2
      ) AS purchase_cvr_7d_avg,

      ROUND(
        purchase_cvr_change_pp,
        2
      ) AS purchase_cvr_change_pp,

      validated_revenue,

      ROUND(
        revenue_7d_avg,
        2
      ) AS revenue_7d_avg,

      ROUND(
        revenue_change_pct,
        2
      ) AS revenue_change_pct,

      ROUND(
        revenue_increment,
        2
      ) AS revenue_increment,

      ROUND(
        SAFE_DIVIDE(
          revenue_increment,
          total_revenue_increment
        ) * 100,
        2
      ) AS revenue_contribution_pct,

      CASE
        WHEN revenue_increment > 0 THEN 'increase'
        WHEN revenue_increment < 0 THEN 'decrease'
        ELSE 'neutral'
      END AS contribution_direction

    FROM contribution

    ORDER BY
      ABS(revenue_contribution_pct) DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "target_date",
                "DATE",
                target_date
            )
        ]
    )

    return execute_logged_query(
        tool_name="analyze_device_landing_rca",
        display_name="Device × Landing Page 교차 분석",
        query=query,
        job_config=job_config,
        arguments={
            "target_date": target_date
        }
    )


# ==================================================
# Funnel RCA
# ==================================================

def analyze_funnel_rca(
    target_date: str,
    device: str,
    landing_page_type: str
):
    """
    특정 날짜 + Device + Landing Page Type 세그먼트의
    Funnel 단계별 RCA 결과를 조회합니다.

    target_date 기준 직전 7일 평균과 비교합니다.
    """

    query = """
    WITH daily_funnel AS (
      SELECT
        date,

        COUNT(*) AS sessions,

        SUM(view_item_flag)
          AS view_item_sessions,

        SUM(add_to_cart_flag)
          AS add_to_cart_sessions,

        SUM(checkout_flag)
          AS checkout_sessions,

        SUM(purchase_flag)
          AS purchase_sessions,

        SAFE_DIVIDE(
          SUM(add_to_cart_flag),
          SUM(view_item_flag)
        ) * 100 AS view_to_cart_pct,

        SAFE_DIVIDE(
          SUM(checkout_flag),
          SUM(add_to_cart_flag)
        ) * 100 AS cart_to_checkout_pct,

        SAFE_DIVIDE(
          SUM(purchase_flag),
          SUM(checkout_flag)
        ) * 100 AS checkout_to_purchase_pct,

        SAFE_DIVIDE(
          SUM(purchase_flag),
          COUNT(*)
        ) * 100 AS purchase_cvr_pct

      FROM `silken-setting-502904-m2.kpi_agent.session_kpi_base`

      WHERE
        date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                 AND @target_date

        AND device = @device

        AND landing_page_type = @landing_page_type

      GROUP BY date
    ),

    baseline AS (
      SELECT
        AVG(sessions)
          AS sessions_7d_avg,

        AVG(view_item_sessions)
          AS view_item_sessions_7d_avg,

        AVG(add_to_cart_sessions)
          AS add_to_cart_sessions_7d_avg,

        AVG(checkout_sessions)
          AS checkout_sessions_7d_avg,

        AVG(purchase_sessions)
          AS purchase_sessions_7d_avg,

        AVG(view_to_cart_pct)
          AS view_to_cart_7d_avg,

        AVG(cart_to_checkout_pct)
          AS cart_to_checkout_7d_avg,

        AVG(checkout_to_purchase_pct)
          AS checkout_to_purchase_7d_avg,

        AVG(purchase_cvr_pct)
          AS purchase_cvr_7d_avg

      FROM daily_funnel

      WHERE date BETWEEN DATE_SUB(@target_date, INTERVAL 7 DAY)
                     AND DATE_SUB(@target_date, INTERVAL 1 DAY)
    ),

    target AS (
      SELECT *
      FROM daily_funnel
      WHERE date = @target_date
    )

    SELECT
      t.sessions,

      ROUND(
        b.sessions_7d_avg,
        2
      ) AS sessions_7d_avg,


      t.view_item_sessions,

      ROUND(
        b.view_item_sessions_7d_avg,
        2
      ) AS view_item_sessions_7d_avg,


      t.add_to_cart_sessions,

      ROUND(
        b.add_to_cart_sessions_7d_avg,
        2
      ) AS add_to_cart_sessions_7d_avg,


      t.checkout_sessions,

      ROUND(
        b.checkout_sessions_7d_avg,
        2
      ) AS checkout_sessions_7d_avg,


      t.purchase_sessions,

      ROUND(
        b.purchase_sessions_7d_avg,
        2
      ) AS purchase_sessions_7d_avg,


      ROUND(
        t.view_to_cart_pct,
        2
      ) AS view_to_cart_pct,

      ROUND(
        b.view_to_cart_7d_avg,
        2
      ) AS view_to_cart_7d_avg,

      ROUND(
        t.view_to_cart_pct
          - b.view_to_cart_7d_avg,
        2
      ) AS view_to_cart_change_pp,


      ROUND(
        t.cart_to_checkout_pct,
        2
      ) AS cart_to_checkout_pct,

      ROUND(
        b.cart_to_checkout_7d_avg,
        2
      ) AS cart_to_checkout_7d_avg,

      ROUND(
        t.cart_to_checkout_pct
          - b.cart_to_checkout_7d_avg,
        2
      ) AS cart_to_checkout_change_pp,


      ROUND(
        t.checkout_to_purchase_pct,
        2
      ) AS checkout_to_purchase_pct,

      ROUND(
        b.checkout_to_purchase_7d_avg,
        2
      ) AS checkout_to_purchase_7d_avg,

      ROUND(
        t.checkout_to_purchase_pct
          - b.checkout_to_purchase_7d_avg,
        2
      ) AS checkout_to_purchase_change_pp,


      ROUND(
        t.purchase_cvr_pct,
        2
      ) AS purchase_cvr_pct,

      ROUND(
        b.purchase_cvr_7d_avg,
        2
      ) AS purchase_cvr_7d_avg,

      ROUND(
        t.purchase_cvr_pct
          - b.purchase_cvr_7d_avg,
        2
      ) AS purchase_cvr_change_pp

    FROM target t

    CROSS JOIN baseline b
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "target_date",
                "DATE",
                target_date
            ),
            bigquery.ScalarQueryParameter(
                "device",
                "STRING",
                device
            ),
            bigquery.ScalarQueryParameter(
                "landing_page_type",
                "STRING",
                landing_page_type
            )
        ]
    )

    return execute_logged_query(
        tool_name="analyze_funnel_rca",
        display_name="핵심 세그먼트 Funnel 분석",
        query=query,
        job_config=job_config,
        arguments={
            "target_date": target_date,
            "device": device,
            "landing_page_type": landing_page_type
        }
    )


# ==================================================
# 단독 테스트
# ==================================================

if __name__ == "__main__":

    clear_query_logs()

    df = analyze_funnel_rca(
        target_date="2021-01-20",
        device="desktop",
        landing_page_type="Home"
    )

    print(
        "\n=============================="
    )

    print(
        "Funnel RCA 결과"
    )

    print(
        "==============================\n"
    )

    print(
        df.to_string(
            index=False
        )
    )

    print(
        "\n=============================="
    )

    print(
        "Query Log"
    )

    print(
        "==============================\n"
    )

    for log in get_query_logs():

        print(
            f"Tool: {log['tool']}"
        )

        print(
            f"Job ID: {log['query_job_id']}"
        )

        print(
            f"Executed At: {log['executed_at']}"
        )

        print(
            f"Rows: {log['row_count']}"
        )

        print(
            f"Bytes Processed: "
            f"{log['total_bytes_processed']}"
        )

        print(
            f"Arguments: {log['arguments']}"
        )

        print()