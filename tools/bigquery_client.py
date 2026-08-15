from google.cloud import bigquery


PROJECT_ID = "silken-setting-502904-m2"


def get_bigquery_client():
    """
    BigQuery 클라이언트를 생성합니다.
    로컬에서는 gcloud ADC 인증 정보를 자동으로 사용합니다.
    """
    return bigquery.Client(project=PROJECT_ID)


def test_connection():
    """
    BigQuery 연결 테스트
    """
    client = get_bigquery_client()

    query = """
    SELECT
        COUNT(*) AS row_count,
        MIN(date) AS min_date,
        MAX(date) AS max_date
    FROM `silken-setting-502904-m2.kpi_agent.kpi_anomaly_monitoring`
    """

    return client.query(query).to_dataframe()


def get_anomaly_by_date(target_date):
    """
    특정 날짜의 KPI 이상 탐지 결과를 조회합니다.
    """

    client = get_bigquery_client()

    query = """
    SELECT
        date,

        sessions,
        sessions_zscore,
        sessions_anomaly,

        purchase_cvr_pct,
        purchase_cvr_zscore,
        purchase_cvr_anomaly,

        view_to_cart_pct,
        view_to_cart_zscore,
        view_to_cart_anomaly,

        validated_revenue,
        revenue_zscore,
        revenue_anomaly,

        anomaly_count,
        any_anomaly

    FROM `silken-setting-502904-m2.kpi_agent.kpi_anomaly_monitoring`

    WHERE date = @target_date
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

    result = client.query(
        query,
        job_config=job_config
    ).to_dataframe()

    return result


if __name__ == "__main__":

    df = get_anomaly_by_date("2021-01-20")

    print(df.to_string(index=False))