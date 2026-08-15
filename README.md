# 📊 KPI Monitoring AI Agent

> 이커머스 핵심 지표를 모니터링하고, 이상 징후가 감지되면 AI Agent가 주요 원인 후보를 단계적으로 분석하여 Daily / Weekly Report까지 제공하는 데이터 분석 프로젝트입니다.

---

## 1. 프로젝트 소개

이커머스 서비스에서는 세션, 전환율, 매출과 같은 핵심 KPI를 지속적으로 모니터링하는 것이 중요합니다.

하지만 일반적인 KPI 대시보드는 지표의 상승·하락을 보여주는 데 그치는 경우가 많고, 실제 원인을 파악하기 위해서는 분석가가 여러 세그먼트와 Funnel을 직접 확인해야 합니다.

본 프로젝트는 이러한 분석 과정을 줄이기 위해 다음 흐름을 구현했습니다.

```text
핵심 지표 모니터링
        ↓
이상 징후 탐지
        ↓
AI Agent 원인 분석
        ↓
분석 쿼리 기록
        ↓
Daily / Weekly Report
```

---

## 2. 주요 기능

- BigQuery 기반 일별 KPI 모니터링
- 최근 7일 평균 대비 편차 + Z-score 기반 이상 탐지
- AI Agent를 활용한 단계적 원인 분석
- Device / Landing Page / Device × Landing Page 분석
- 핵심 세그먼트 Funnel 분석
- 실제 실행 BigQuery SQL 및 Job ID 기록
- Revenue 데이터 품질 검증
- Streamlit 기반 모니터링 화면
- Daily / Weekly PDF Report 생성

---

## 3. 사용 데이터

Google Analytics 4의 **E-commerce Sample Dataset**을 사용했습니다.

| 항목 | 내용 |
|---|---|
| 데이터 소스 | BigQuery Public Dataset |
| Dataset | `ga4_obfuscated_sample_ecommerce` |
| 기간 | `2020-11-01 ~ 2021-01-31` |
| 데이터 형태 | GA4 이벤트 단위 로그 데이터 |

### 주요 이벤트

```text
session_start
view_item
add_to_cart
begin_checkout
purchase
```

원천 이벤트 데이터를 그대로 사용하지 않고, 분석 목적에 맞게 세션 단위 및 일별 KPI 단위로 가공했습니다.

```text
GA4 이벤트 데이터
        ↓
session_kpi_base
        ↓
daily_kpi_monitoring
        ↓
kpi_anomaly_monitoring
        ↓
AI Agent 원인 분석
```

---

## 4. 핵심 KPI

이커머스의 **유입 → 구매 의도 → 최종 전환 → 매출 성과**를 함께 모니터링하기 위해 4개의 핵심 KPI를 정의했습니다.

| 구분 | KPI | 목적 |
|---|---|---|
| 유입 | 세션 수 | 전체 트래픽 규모 및 변화 확인 |
| 구매 의도 | 조회 → 장바구니 전환율 | 상품 조회가 구매 의도로 이어지는 정도 확인 |
| 최종 전환 | 구매 전환율 | 전체 방문 중 구매까지 완료된 비율 확인 |
| 비즈니스 성과 | 유효 매출 | 실제 매출 성과의 변화 확인 |

### 세션 정의

```sql
CONCAT(
    user_pseudo_id,
    '-',
    CAST(ga_session_id AS STRING)
) AS session_key
```

`session_start` 이벤트가 존재하는 세션만 포함하며, 동일 세션에 여러 `session_start`가 존재할 경우 가장 이른 이벤트를 기준으로 중복을 제거했습니다.

### 구매 전환율

```text
구매 전환율
= 구매 세션 / 전체 세션 × 100
```

구매 세션은 `purchase` 이벤트가 1회 이상 발생한 세션으로 정의했습니다.

### 유효 매출

유효한 `transaction_id`를 가진 주문만 사용하고, 동일 세션 내 동일 `transaction_id`가 중복된 경우 하나의 주문으로 처리했습니다.

또한 Transaction Coverage가 기준을 충족한 경우에만 Revenue 이상 탐지에 사용했습니다.

---

## 5. 이상 탐지

일별 KPI가 최근 패턴에서 크게 벗어났는지 판단하기 위해 두 가지 기준을 함께 사용했습니다.

```text
|Z-score| ≥ 2.0
AND
|최근 7일 평균 대비 편차| ≥ 30%
```

### 최근 7일 평균 대비 편차

```text
(당일 KPI - 최근 7일 평균)
──────────────────────── × 100
       최근 7일 평균
```

### Z-score

```text
당일 KPI - 최근 7일 평균
────────────────────────
    최근 7일 표준편차
```

두 조건을 함께 적용해 단순 변화폭뿐 아니라 최근 데이터의 변동성까지 고려했습니다.

Streamlit 화면에서는 사용자가 쉽게 이해할 수 있도록 Z-score를 **이상 점수**로 표현했습니다.

---

## 6. AI Agent 설계

본 프로젝트에서 AI Agent는 KPI 수치를 직접 계산하지 않습니다.

> **SQL / Python은 실제 수치 계산을 담당하고, AI Agent는 계산된 결과를 기반으로 다음 분석 단계를 판단합니다.**

이상 징후가 발생하면 다음 순서로 분석 범위를 좁혀갑니다.

```text
이상 KPI 확인
      ↓
Device별 영향 분석
      ↓
Landing Page별 영향 분석
      ↓
Device × Landing Page 교차 분석
      ↓
핵심 세그먼트 Funnel 분석
      ↓
주요 원인 후보 정리
```

### Agent Tools

```text
get_anomaly_by_date
        ↓
analyze_device_rca
        ↓
analyze_landing_page_type_rca
        ↓
analyze_device_landing_rca
        ↓
analyze_funnel_rca
```

각 Tool은 BigQuery SQL을 실행하여 실제 계산 결과를 Agent에게 반환합니다.

Agent는 결과를 바탕으로 영향력이 높은 세그먼트를 선택하고 다음 분석을 수행합니다.

---

## 7. 실제 분석 사례

### 2021-01-20

해당 날짜에는 다음 KPI에서 이상 상승이 탐지되었습니다.

| KPI | 값 | 이상 점수 | 상태 |
|---|---:|---:|---|
| 구매 전환율 | 1.99% | 4.63 | 이상 상승 |
| 유효 매출 | 6,599 | 5.34 | 이상 상승 |
| 세션 수 | 4,727 | 1.61 | 정상 |
| 조회 → 장바구니 전환율 | 20.32% | -1.32 | 정상 |

### 주요 원인 후보

#### Device

```text
Desktop
Revenue Contribution: 56.97%
Sessions 변화: +25.52%
Purchase CVR 변화: +1.29%p
```

#### Landing Page

```text
Home
Revenue Contribution: 67.86%
```

#### Device × Landing Page

```text
Desktop × Home

Revenue Contribution: 41.44%
Sessions 변화: +31.23%
Purchase CVR 변화: +2.00%p
```

### 핵심 세그먼트 Funnel 변화

| Funnel 단계 | 당일 | 최근 7일 평균 대비 |
|---|---:|---:|
| 조회 → 장바구니 | 32.10% | +2.86%p |
| 장바구니 → 결제 시작 | 63.22% | +15.93%p |
| 결제 시작 → 구매 | 65.45% | +22.81%p |
| 전체 구매 전환율 | 2.94% | +2.00%p |

분석 결과, `Desktop × Home` 세그먼트에서 유입 증가와 함께 하단 Funnel 전환율이 개선된 것이 구매 전환율 및 매출 상승에 크게 기여한 **주요 원인 후보**로 확인되었습니다.

---

## 8. 분석 쿼리 기록

AI Agent가 분석 과정에서 실행한 SQL의 근거를 확인할 수 있도록 Query Log를 기록합니다.

각 분석 단계에서 다음 정보를 저장합니다.

```text
분석 단계
분석 조건
실행 SQL
BigQuery Job ID
조회 결과 행 수
처리 데이터 정보
```

이를 통해 다음이 가능하도록 설계했습니다.

- AI 분석 결과의 근거 확인
- 실제 실행 SQL 재현
- Agent의 분석 순서 추적
- LLM 결과와 실제 계산 결과 분리

---

## 9. 데이터 품질 관리

Revenue의 경우 데이터 누락이나 주문 식별 문제로 인해 잘못된 이상 탐지가 발생할 수 있어 별도의 품질 기준을 적용했습니다.

```text
Transaction Coverage ≥ 80%
```

기준을 충족하지 못한 Revenue 데이터는 이상 탐지 대상에서 제외합니다.

Streamlit에서는 다음 정보를 별도로 확인할 수 있습니다.

- 기준 데이터 일수
- Revenue 유효 기준 일수
- Revenue 데이터 유효 여부
- 이상 탐지 가능 여부

---

## 10. Daily / Weekly Report

분석 결과를 공유 가능한 형태로 제공하기 위해 PDF Report를 생성합니다.

### Daily Report

- 핵심 KPI 요약
- 이상 징후
- AI 원인 분석
- 핵심 세그먼트 Funnel 변화
- 데이터 품질
- 분석 기준

### Weekly Report

- 주간 KPI 요약
- KPI 변화 추이
- 일별 KPI 현황
- 주간 이상 징후
- 주요 이상 발생일
- 주요 원인 후보
- 핵심 세그먼트 Funnel 변화
- 주간 데이터 품질

---

## 11. 기술 스택

### Data / Analysis

- BigQuery
- SQL
- Python
- Pandas

### AI

- OpenAI API
- Tool Calling

### Visualization / Application

- Streamlit
- Altair

### Reporting

- ReportLab

---

## 12. 프로젝트 구조

```text
kpi-monitoring-ai-agent/
│
├── agent/
│   ├── __init__.py
│   └── agent.py
│
├── prompts/
│   └── system_prompt.py
│
├── reports/
│   ├── __init__.py
│   └── report_generator.py
│
├── tools/
│   ├── __init__.py
│   ├── bigquery_client.py
│   └── rca_tools.py
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

### 주요 모듈

| 파일 | 역할 |
|---|---|
| `app.py` | Streamlit UI |
| `agent/agent.py` | AI Agent 실행 및 Tool Calling |
| `tools/bigquery_client.py` | BigQuery 연결 및 KPI 조회 |
| `tools/rca_tools.py` | Device / Landing / Funnel 원인 분석 |
| `prompts/system_prompt.py` | AI Agent 분석 원칙 |
| `reports/report_generator.py` | Daily / Weekly PDF 생성 |

---

## 13. 실행 방법

### 1. Repository Clone

```bash
git clone https://github.com/kyj-da/kpi-monitoring-ai-agent.git
cd kpi-monitoring-ai-agent
```

### 2. 가상환경 생성

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

프로젝트 최상위 폴더에 `.env` 파일을 생성합니다.

```env
OPENAI_API_KEY=your_openai_api_key
```

> `.env` 파일은 GitHub에 업로드하지 않습니다.

### 5. Google Cloud 인증

BigQuery에 접근할 수 있도록 Google Cloud Application Default Credentials를 설정합니다.

### 6. Streamlit 실행

```bash
python -m streamlit run app.py
```

---

## 14. 한계 및 개선 방향

### 한계

사용한 데이터는 GA4 행동 이벤트 중심의 공개 샘플 데이터이므로 다음과 같은 실제 비즈니스 정보는 포함되어 있지 않습니다.

- 프로모션
- 광고 캠페인 변경
- 가격 변경
- UI / UX 변경
- 서비스 장애
- 재고 상황

따라서 Agent는 **어떤 세그먼트와 Funnel 구간이 KPI 변화에 크게 기여했는지**는 분석할 수 있지만, 실제 비즈니스 원인을 직접 확정하지는 않습니다.

이에 분석 결과에서도 `원인`이 아닌 **`주요 원인 후보`**로 표현합니다.

### 개선 방향

실제 서비스 환경에서는 다음 데이터를 추가로 연결할 수 있습니다.

```text
GA4 행동 데이터
        +
CRM 데이터
        +
캠페인 데이터
        +
프로모션 정보
        +
서비스 변경 / 장애 로그
        ↓
AI Agent 분석 범위 확장
```

또한 장기간 데이터가 확보될 경우 KPI별 특성과 계절성을 반영한 이상 탐지 모델로 확장할 수 있습니다.

---

## 15. 프로젝트 핵심

> **KPI 모니터링 → 이상 탐지 → AI Agent 원인 분석 → 분석 근거 추적 → 리포팅을 하나의 데이터 분석 흐름으로 연결했습니다.**

> **LLM이 수치를 직접 계산하지 않고, SQL/Python의 실제 계산 결과를 기반으로 다음 분석 단계를 판단하도록 설계한 것이 핵심입니다.**
