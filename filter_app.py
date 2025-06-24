import streamlit as st
import pandas as pd
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

st.set_page_config(page_title="엑셀 데이터 필터링", layout="wide")
st.title("📊 엑셀 데이터 다중 조건 필터")

uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xls", "xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.subheader("데이터 미리보기")
    st.write(df.head())

    st.subheader("필터 조건 설정")
    filter_columns = st.multiselect("필터할 컬럼 선택", df.columns)
    filtered_df = df.copy()
    for col in filter_columns:
        unique_vals = df[col].unique().tolist()
        selected_vals = st.multiselect(f"{col} 값 선택", unique_vals)
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

    st.subheader("필터링 결과")
    st.write(filtered_df)

    if st.checkbox("LLM에게 요약 요청"):
        openai_api_key = st.text_input("OpenAI API Key를 입력하세요", type="password")
        if openai_api_key:
            llm = ChatOpenAI(api_key=openai_api_key)
            system_msg = SystemMessage(content="너는 데이터 분석 도우미야. 사용자에게 친절하게 답변해.")
            user_msg = HumanMessage(content=f"다음 데이터에 대한 간단한 요약을 해줘:\n{filtered_df.head().to_string()}")
            response = llm.invoke([system_msg, user_msg])
            st.write(response.content)
        else:
            st.warning("OpenAI API Key를 입력해주세요.")
