from google.cloud import bigquery
from google.oauth2 import service_account


PROJECT_ID = "silken-setting-502904-m2"


def get_bigquery_client():
    """
    BigQuery 클라이언트를 생성합니다.

    - Streamlit Cloud:
      st.secrets["gcp_service_account"]의 서비스 계정 인증 사용

    - 로컬 환경:
      기존 Google Application Default Credentials(ADC) 사용
    """

    # Streamlit Cloud 서비스 계정 인증 시도
    try:
        import streamlit as st

        if "gcp_service_account" in st.secrets:
            service_account_info = dict(
                st.secrets["gcp_service_account"]
            )

            credentials = (
                service_account.Credentials.from_service_account_info(
                    service_account_info
                )
            )

            return bigquery.Client(
                project=PROJECT_ID,
                credentials=credentials,
            )

    except Exception:
        # 로컬 실행 시 st.secrets가 없어도 ADC로 실행
        pass

    # 로컬 환경: gcloud ADC 인증
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
                target_date,
            )
        ]
    )

    result = client.query(
        query,
        job_config=job_config,
    ).to_dataframe()

    return result


if __name__ == "__main__":

    df = get_anomaly_by_date("2021-01-20")

    print(df.to_string(index=False))