import streamlit as st
import pandas as pd
import openai
import os
from fpdf import FPDF
from datetime import datetime

openai.api_key = st.secrets['OPENAI_API_KEY']

st.set_page_config(page_title="하수처리장 데이터 분석기", layout="wide")
st.title("💧 하수/폐수처리장 시계열 데이터 분석기")

# Step 1: 기본 사업장 정보 입력
st.header("1️⃣ 사업장 기본 정보 입력")
business_name = st.text_input("사업장명")
location = st.text_input("위치 (예: 전라남도 순천시)")
process_name = st.text_input("공법 명칭")
process_desc = st.text_area("공정 설명 (300자 이내)", max_chars=300)

# Step 2: 엑셀 파일 업로드 및 설명 입력
st.header("2️⃣ 엑셀 시계열 데이터 업로드")
uploaded_files = st.file_uploader("엑셀 파일 (최대 10개)", type=["xls", "xlsx"], accept_multiple_files=True)

dataframes = {}
descriptions = {}

if uploaded_files:
    for file in uploaded_files:
        with st.expander(f"📁 {file.name} - 설명 및 미리보기"):
            desc = st.text_area(f"설명 (100자 이내)", max_chars=100, key=f"desc_{file.name}")
            df = pd.read_excel(file)
            st.write("미리보기:", df.head())
            dataframes[file.name] = df
            descriptions[file.name] = desc

# Step 3: AI 정형화 및 사용자 확인
if st.button("🔧 AI에게 정형화 방식 요청"):
    st.header("3️⃣ 정형화 제안")
    summaries = {}
    for fname, df in dataframes.items():
        prompt = f"""
업로드된 시계열 데이터 파일 이름: {fname}
파일 설명: {descriptions[fname]}
다음은 최근 데이터 샘플입니다:
{df.tail().to_string(index=False)}

이 데이터를 분석에 활용하기 위해 '시간, 항목1, 항목2…' 형태로 어떻게 정형화하면 좋을지 제안해 주세요.
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 숙련된 데이터 정제 전문가입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response['choices'][0]['message']['content']
        summaries[fname] = summary
        st.subheader(f"📄 {fname} 정형화 제안")
        st.markdown(summary)

    if st.button("✅ 정형화 확인 및 최종 분석 시작"):
        st.header("4️⃣ GPT-4 최종 분석")
        combined_prompt = f"""
다음은 하수/폐수 처리장의 시계열 자료입니다. 각 공정 데이터와 수질 측정 데이터를 기반으로 추세, 상관관계, 영향성을 분석해 주세요.

📌 사업장명: {business_name}
📌 위치: {location}
📌 공법: {process_name}
📌 공정 설명: {process_desc}
"""
        for fname in dataframes:
            combined_prompt += f"\n---\n📁 파일: {fname}\n📄 설명: {descriptions[fname]}\n📄 정형화 제안: {summaries[fname]}\n📊 최근 데이터:\n{dataframes[fname].tail().to_string(index=False)}\n"

        final_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 숙련된 환경 데이터 분석가입니다."},
                {"role": "user", "content": combined_prompt}
            ]
        )

        analysis_result = final_response['choices'][0]['message']['content']
        st.success("✅ 분석 완료")
        st.markdown(analysis_result)

        # Step 5: PDF 저장 기능
        if st.button("📄 PDF로 결과 저장"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, f"하수처리장 분석 리포트\n\n사업장명: {business_name}\n위치: {location}\n공법: {process_name}\n\n공정 설명:\n{process_desc}\n\n분석 결과:\n{analysis_result}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_report_{timestamp}.pdf"
            pdf.output(filename)
            with open(filename, "rb") as f:
                st.download_button(
                    label="📥 리포트 다운로드",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
            os.remove(filename)
