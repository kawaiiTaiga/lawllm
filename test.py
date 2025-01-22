import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np
import random
import time
from generate import *
import traceback

@st.cache_resource
def load_model():
    model_id = "MLP-KTLim/llama-3-Korean-Bllossom-8B"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id).cuda()
    return tokenizer, model




def main():
    st.title("문서 법률 자문 시스템(DEMO)")

    tokenizer, model = load_model()

    # 세션 상태 초기화
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "task_data" not in st.session_state:
        st.session_state.task_data = {}
    if "selected_issue" not in st.session_state:
        st.session_state.selected_issue = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

    # 단계별 태스크 정의
    tasks = [
        "문서입력",
        "법적 위험요소 파악",
        "실제 법률과 비교",
        "결과 확인"
    ]

    # 현재 단계 표시
    st.write(f"현재 단계: {tasks[st.session_state.step]}")

    # 단계별 로직
    if st.session_state.step == 0:
        document = st.text_area("법적 검토가 필요한 문서를 입력하세요:", height=200)
        if st.button("검토 시작"):
            if document:
                with st.spinner("문서를 분석 중입니다..."):
                    st.session_state.task_data["document"] = document
                    result, messages = Avaliable_Law_Issue(model, tokenizer, document)
                    st.session_state.task_data["Avaliable_law_issues"] = result
                    st.session_state.task_data["Document_message"] = messages
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("문서를 입력해주세요.")

    elif st.session_state.step == 1:
        st.session_state.returntomenu = True 
        st.write("분석 결과:")
        st.write("## 잠재적 법적 문제")
        result = st.session_state.task_data["Avaliable_law_issues"]
        for i, issue in enumerate(result["potential_legal_issues"]):
            with st.expander(f"문제 {i+1}: {issue['issue_type']}"):
                st.markdown(f"""
                <div style="border:1px solid #e0e0e0; border-radius:5px; padding:10px; margin-bottom:10px;">
                    <p><strong>문제 부분:</strong> {issue['issue_part']}</p>
                    <p><strong>설명:</strong> {issue['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"문제 {i+1} 분석", key=f"analyze_button_{i}"):
                    st.session_state.selected_issue = i
                    st.session_state.step = 2
                    st.session_state.analysis_result = None
                    st.session_state.task_data.pop('Law_keyword', None)
                    st.session_state.task_data.pop('found_result', None)
                    st.session_state.task_data.pop('Related_Laws', None)
                    st.rerun()

        if st.button("다시 시작"):
            st.session_state.step = 0
            st.session_state.task_data = {}
            st.session_state.selected_issue = None
            st.session_state.analysis_result = None
            st.rerun()
    elif st.session_state.step == 2:
        issue = st.session_state.task_data["Avaliable_law_issues"]["potential_legal_issues"][st.session_state.selected_issue]
        st.write(f"## 선택된 문제: {issue['issue_type']}")
        st.write(f"문제 부분: {issue['issue_part']}")
        st.write(f"설명: {issue['description']}")

        @st.cache_data
        def search_laws():
            messages = st.session_state.task_data["Document_message"]
            try:
                law_keyword, found_result = Search_Laws(model, tokenizer, st.session_state.selected_issue, messages)
                st.session_state.task_data['Law_keyword'] = law_keyword
                st.session_state.task_data['found_result'] = found_result
            except Exception as e:
                st.error(f"법률 검색 중 오류가 발생했습니다: {str(e)}")
                st.session_state.task_data['Law_keyword'] = "검색 실패"
                st.session_state.task_data['found_result'] = None

        @st.cache_data
        def select_laws():
            messages = st.session_state.task_data["Document_message"]
            try:  
                st.session_state.task_data['Related_Laws'] = Select_Laws(model,tokenizer, st.session_state.selected_issue, messages, st.session_state.task_data['found_result'])
            except Exception as e:
                st.error(f"법률 검색 중 오류가 발생했습니다: {str(e)}")
                st.session_state.task_data['Related_Laws'] = "선택 실패"

        search_laws()
        st.write("## 검색 키워드")
        st.text(st.session_state.task_data['Law_keyword'])
        select_laws()
        st.write("## 검색 결과")

        if 'selected_laws' not in st.session_state:
            st.session_state.selected_laws = []
            st.session_state.selected_law_ids = []

        for law, law_id in zip(st.session_state.task_data['Related_Laws']['related_law_list'], 
                               st.session_state.task_data['Related_Laws']['related_law_id_list']):
            if st.button(law):
                if law in st.session_state.selected_laws:
                    index = st.session_state.selected_laws.index(law)
                    st.session_state.selected_laws.pop(index)
                    st.session_state.selected_law_ids.pop(index)
                else:
                    st.session_state.selected_laws.append(law)
                    st.session_state.selected_law_ids.append(law_id)

        st.write("## 선택된 법률")
        for law in st.session_state.selected_laws:
            st.write(law)

        if st.button("다시생성"):
            st.session_state.task_data.pop('Law_keyword', None)
            st.session_state.task_data.pop('found_result', None)
            st.session_state.task_data.pop('Related_Laws', None)
            st.session_state.selected_laws = []
            st.session_state.selected_law_ids = []
            st.cache_data.clear()
            st.rerun()

        if st.button("이전단계"):
            st.session_state.step = 1
            st.session_state.task_data.pop('Law_keyword', None)
            st.session_state.task_data.pop('found_result', None)
            st.session_state.task_data.pop('Related_Laws', None)
            st.session_state.selected_laws = []
            st.session_state.selected_law_ids = []
            st.cache_data.clear()
            st.rerun()

        if st.button("다음단계"):
            if st.session_state.selected_laws:
                st.session_state.step = 3
                st.rerun()
            else:
                st.warning("다음 단계로 진행하기 전에 최소한 하나의 법률을 선택해주세요.")

    elif st.session_state.step == 3:
        st.write("## 선택된 법률 상세 정보")

        if not st.session_state.selected_laws or not st.session_state.selected_law_ids:
            st.warning("선택된 법률이 없습니다. 이전 단계로 돌아가 법률을 선택해주세요.")
            if st.button("이전 단계로 돌아가기"):
                st.session_state.step = 2
                st.rerun()
        else:
            if 'law_details' not in st.session_state:
                st.session_state.law_details = {}

            for law, law_id in zip(st.session_state.selected_laws, st.session_state.selected_law_ids):
                if law_id not in st.session_state.law_details:
                    with st.spinner(f"{law} 상세 정보를 가져오는 중..."):
                        try:
                            #print(st.session_state.task_data["Avaliable_law_issues"]['potential_legal_issues'][st.session_state.selected_issue])
                            details = search_detail(model, tokenizer, law_id,st.session_state.task_data["Avaliable_law_issues"]['potential_legal_issues'][st.session_state.selected_issue])
                            st.session_state.law_details[law_id] = details
                        except Exception as e:
                            st.error(f"{law} 상세 정보를 가져오는 데 실패했습니다: {str(e)}")
                            st.error(f"에러 상세: {traceback.format_exc()}")
                            continue

                st.subheader(law)
                details = st.session_state.law_details[law_id]

                if details and 'related_articles' in details and details['related_articles']:
                    for article in details['related_articles']:
                        with st.expander(f"제{article['article_number']}조"):
                            st.write(f"관련 이유: {article['reason']}")
                else:
                    st.write("이 법률에 대한 관련 조항 정보가 없습니다.")
            

                            


            if st.button("이전 단계로 돌아가기"):
                st.session_state.step = 2
                st.session_state.law_details = {}  # 상세 정보 초기화
                st.rerun()


    st.write("Session State:", st.session_state)
if __name__ == "__main__":
    main()