import os
import json

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from prompts.system_prompt import SYSTEM_PROMPT
from tools.bigquery_client import get_anomaly_by_date
from tools.rca_tools import (
    analyze_device_rca,
    analyze_landing_page_type_rca,
    analyze_device_landing_rca,
    analyze_funnel_rca,
    clear_query_logs,
    get_query_logs,
)


# --------------------------------------------------
# 환경변수 / OpenAI Client
# --------------------------------------------------

load_dotenv()


def get_openai_api_key():
    """
    OpenAI API Key를 가져옵니다.

    - Streamlit Cloud:
      st.secrets["OPENAI_API_KEY"] 사용

    - 로컬 환경:
      .env의 OPENAI_API_KEY 사용
    """

    # Streamlit Cloud
    try:
        import streamlit as st

        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]

    except Exception:
        pass

    # 로컬 .env
    return os.getenv("OPENAI_API_KEY")


api_key = get_openai_api_key()

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY가 설정되어 있지 않습니다."
    )

client = OpenAI(
    api_key=api_key
)


# --------------------------------------------------
# OpenAI Function Tools 정의
# --------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "name": "get_anomaly_by_date",
        "description": (
            "특정 날짜의 KPI 이상 탐지 결과를 조회합니다. "
            "분석을 시작할 때 어떤 KPI에 이상이 발생했는지 확인하기 위해 사용합니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "분석 날짜. YYYY-MM-DD 형식"
                }
            },
            "required": ["target_date"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "analyze_device_rca",
        "description": (
            "특정 날짜의 Device별 KPI 변화를 직전 7일 평균과 비교합니다. "
            "desktop, mobile, tablet 중 어떤 Device가 변화에 크게 기여했는지 분석합니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "분석 날짜. YYYY-MM-DD 형식"
                }
            },
            "required": ["target_date"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "analyze_landing_page_type_rca",
        "description": (
            "특정 날짜의 Landing Page Type별 KPI 변화를 직전 7일 평균과 비교합니다. "
            "Home, Category, Product Detail 등의 Landing Page 유형별 기여도를 분석합니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "분석 날짜. YYYY-MM-DD 형식"
                }
            },
            "required": ["target_date"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "analyze_device_landing_rca",
        "description": (
            "특정 날짜의 Device × Landing Page Type 조합별 KPI 변화를 분석합니다. "
            "전체 Revenue 변화에 가장 크게 기여한 구체적인 세그먼트를 찾기 위해 사용합니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "분석 날짜. YYYY-MM-DD 형식"
                }
            },
            "required": ["target_date"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "analyze_funnel_rca",
        "description": (
            "특정 날짜와 Device × Landing Page Type 세그먼트에서 "
            "View Item → Add to Cart → Checkout → Purchase Funnel 변화를 분석합니다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "분석 날짜. YYYY-MM-DD 형식"
                },
                "device": {
                    "type": "string",
                    "description": "분석할 Device. 예: desktop, mobile, tablet"
                },
                "landing_page_type": {
                    "type": "string",
                    "description": "분석할 Landing Page Type. 예: Home, Category"
                }
            },
            "required": [
                "target_date",
                "device",
                "landing_page_type"
            ],
            "additionalProperties": False
        }
    }
]


# --------------------------------------------------
# pandas DataFrame → JSON 문자열
# --------------------------------------------------

def dataframe_to_json(df):
    """
    Tool 결과인 pandas DataFrame을
    모델에 전달 가능한 JSON 문자열로 변환합니다.
    """

    if df.empty:
        return json.dumps(
            {
                "status": "no_data",
                "rows": []
            },
            ensure_ascii=False
        )

    rows = df.to_dict(
        orient="records"
    )

    return json.dumps(
        {
            "status": "success",
            "rows": rows
        },
        ensure_ascii=False,
        default=str
    )


# --------------------------------------------------
# Tool 실제 실행
# --------------------------------------------------

def execute_tool(
    tool_name,
    arguments
):
    """
    OpenAI가 선택한 Tool을 실제 Python 함수와 연결합니다.
    """

    if tool_name == "get_anomaly_by_date":

        df = get_anomaly_by_date(
            arguments["target_date"]
        )

        return dataframe_to_json(
            df
        )


    if tool_name == "analyze_device_rca":

        df = analyze_device_rca(
            arguments["target_date"]
        )

        return dataframe_to_json(
            df
        )


    if tool_name == "analyze_landing_page_type_rca":

        df = analyze_landing_page_type_rca(
            arguments["target_date"]
        )

        return dataframe_to_json(
            df
        )


    if tool_name == "analyze_device_landing_rca":

        df = analyze_device_landing_rca(
            arguments["target_date"]
        )

        # 모델 입력량 제한을 위해
        # 상위 10개 세그먼트만 전달
        df = df.head(
            10
        )

        return dataframe_to_json(
            df
        )


    if tool_name == "analyze_funnel_rca":

        df = analyze_funnel_rca(
            target_date=arguments[
                "target_date"
            ],
            device=arguments[
                "device"
            ],
            landing_page_type=arguments[
                "landing_page_type"
            ]
        )

        return dataframe_to_json(
            df
        )


    raise ValueError(
        f"알 수 없는 Tool입니다: {tool_name}"
    )


# --------------------------------------------------
# Agent Log 저장
# --------------------------------------------------

def save_analysis_log(
    target_date: str,
    analysis_path: list,
    query_logs: list,
    final_result: str
):
    """
    Agent의 분석 경로,
    실제 BigQuery Query Log,
    최종 RCA 결과를 JSON 파일로 저장합니다.
    """

    log_dir = Path(
        "logs"
    )

    log_dir.mkdir(
        exist_ok=True
    )

    now = (
        datetime
        .now()
        .astimezone()
    )

    timestamp = now.strftime(
        "%Y%m%d_%H%M%S"
    )

    log_data = {
        "target_date": target_date,

        "created_at": now.isoformat(
            timespec="seconds"
        ),

        "analysis_path": analysis_path,

        "query_logs": query_logs,

        "final_result": final_result
    }

    file_path = (
        log_dir
        / f"rca_{target_date}_{timestamp}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            log_data,
            f,
            ensure_ascii=False,
            indent=2,
            default=str
        )

    return str(
        file_path
    )


# --------------------------------------------------
# KPI Monitoring Agent
# --------------------------------------------------

def run_kpi_agent(
    target_date: str
):

    # ==================================================
    # 새로운 분석 시작
    # 기존 Query Log 초기화
    # ==================================================

    clear_query_logs()


    user_request = f"""
    {target_date}의 KPI 이상 징후를 분석해주세요.

    이상 KPI를 먼저 확인한 뒤,
    필요한 RCA 도구를 단계적으로 사용하여
    주요 원인 후보를 분석해주세요.
    """


    # Agent가 어떤 Tool을 어떤 순서로 사용했는지 기록
    analysis_path = []


    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        input=user_request,
        tools=TOOLS
    )


    while True:

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]


        # ==================================================
        # 더 이상 Tool 호출이 없으면 최종 응답
        # ==================================================

        if not tool_calls:

            final_result = (
                response.output_text
            )

            # RCA Tool들이 실행하며 누적한
            # 실제 BigQuery Query Log 조회
            query_logs = (
                get_query_logs()
            )

            log_file = save_analysis_log(
                target_date=target_date,
                analysis_path=analysis_path,
                query_logs=query_logs,
                final_result=final_result
            )

            print(
                f"\n[로그 저장 완료] "
                f"{log_file}"
            )

            print(
                f"[Query Log 저장] "
                f"{len(query_logs)}개"
            )

            return final_result


        # ==================================================
        # Tool 실행
        # ==================================================

        tool_outputs = []


        for tool_call in tool_calls:

            tool_name = (
                tool_call.name
            )

            arguments = json.loads(
                tool_call.arguments
            )


            print(
                f"\n[Tool 실행] "
                f"{tool_name}"
            )

            print(
                f"[Arguments] "
                f"{arguments}"
            )


            # ----------------------------------------------
            # Agent 분석 경로 기록
            # ----------------------------------------------

            analysis_path.append(
                {
                    "tool": tool_name,
                    "arguments": arguments
                }
            )


            # ----------------------------------------------
            # 실제 Tool 실행
            # ----------------------------------------------

            result = execute_tool(
                tool_name,
                arguments
            )


            # ----------------------------------------------
            # Tool 실행 결과를 OpenAI에 반환
            # ----------------------------------------------

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": (
                        tool_call.call_id
                    ),
                    "output": result
                }
            )


        # ==================================================
        # Tool 결과 기반 다음 Agent 판단
        # ==================================================

        response = client.responses.create(
            model="gpt-5.6-luna",
            instructions=SYSTEM_PROMPT,
            previous_response_id=(
                response.id
            ),
            input=tool_outputs,
            tools=TOOLS
        )


# --------------------------------------------------
# 테스트
# --------------------------------------------------

if __name__ == "__main__":

    result = run_kpi_agent(
        "2021-01-20"
    )

    print(
        "\n=============================="
    )

    print(
        "최종 RCA 결과"
    )

    print(
        "==============================\n"
    )

    print(
        result
    )