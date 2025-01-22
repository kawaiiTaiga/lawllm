import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from generate import *
import traceback


# 상수 정의
TASKS = [
    "문서입력",
    "법적 위험요소 파악",
    "실제 법률과 비교",
    "결과 확인"
]

def initialize_session_state():
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "task_data" not in st.session_state:
        st.session_state.task_data = {}
    if "selected_issue" not in st.session_state:
        st.session_state.selected_issue = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "selected_laws" not in st.session_state:
        st.session_state.selected_laws = []
    if "selected_law_ids" not in st.session_state:
        st.session_state.selected_law_ids = []
    # 'law_details'가 없으면 빈 딕셔너리로 초기화
    if "law_details" not in st.session_state:
        st.session_state.law_details = {}
def apply_custom_css():
    st.markdown("""
    <style>
    .sidebar-item {
        margin-left: 20px;
        padding: 5px 0;
        transition: color 0.3s;
    }
    .sidebar-item::before {
        content: "";
        position: absolute;
        left: -10px;
        top: 50%;
        height: 100%;
        width: 1px;
        background-color: #555;
        transform: translateX(-50%);
    }
    .sidebar-item-selected {
        font-weight: bold;
        color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

def sidebar_item(label, level=0, selected=False):
    margin_left = 20 * level
    selected_class = "sidebar-item-selected" if selected else ""
    return st.markdown(f"""
    <div class="sidebar-item {selected_class}" style="margin-left: {margin_left}px;">
        {label}
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    apply_custom_css()
    
    with st.sidebar:
        st.header("분석 진행 상황")
        
        # 단계 1: 문서 입력
        sidebar_item("1. 문서 입력", selected=(st.session_state.step == 0))
        
        # 단계 2: 잠재적 법적 문제
        if "Avaliable_law_issues" in st.session_state.task_data:
            sidebar_item("2. 잠재적 법적 문제", selected=(st.session_state.step == 1))
            
            issues = st.session_state.task_data["Avaliable_law_issues"]["potential_legal_issues"]
            for i, issue in enumerate(issues):
                issue_text = f"문제 {i+1}: {issue['issue_type']}"
                sidebar_item(issue_text, level=1, 
                             selected=(i == st.session_state.selected_issue and st.session_state.step >= 2))
                
                if i == st.session_state.selected_issue and st.session_state.step >= 2:
                    # 단계 3: 관련 법률
                    if 'selected_laws' in st.session_state and st.session_state.selected_laws:
                        sidebar_item("3. 관련 법률", level=1, selected=(st.session_state.step >= 3))
                        
                        for j, law in enumerate(st.session_state.selected_laws):
                            sidebar_item(law, level=2)
                            
                            # 단계 4: 관련 조항
                            if 'law_details' in st.session_state and isinstance(st.session_state.law_details, dict):
                                law_id = st.session_state.selected_law_ids[j] if j < len(st.session_state.selected_law_ids) else None
                                if law_id:
                                    details = st.session_state.law_details.get(law_id, {})
                                    if 'related_articles' in details:
                                        for article in details['related_articles']:
                                            sidebar_item(article['article_number'], level=3)
        
        st.markdown("---")
        st.markdown(f"**현재 단계:** {TASKS[st.session_state.step]}")
def display_header():
    st.markdown(
        """
        <style>
        .big-font {
            font-size:30px !important;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<p class="big-font">문서 법률 자문 시스템 (DEMO)</p>', unsafe_allow_html=True)
    st.progress((st.session_state.step + 1) / len(TASKS))
    st.markdown(f"**현재 단계: {TASKS[st.session_state.step]}**")

def document_input(tokenizer, model):
    st.markdown("### 문서 입력")
    document = st.text_area("법적 검토가 필요한 문서를 입력하세요:", height=200)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("검토 시작", key="start_review"):
            if document:
                with st.spinner("문서를 분석 중입니다..."):
                    st.session_state.task_data["document"] = document
                    result, messages = Avaliable_Law_Issue(model, tokenizer, document)
                    st.session_state.task_data["Avaliable_law_issues"] = result
                    st.session_state.task_data["Document_message"] = messages
                    
                    # 기록 추가
                    st.session_state.history.append({
                        "단계": TASKS[st.session_state.step],
                        "입력 문서": document,
                        "분석 결과": result
                    })
                    
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("문서를 입력해주세요.")

def display_potential_issues():
    st.markdown("### 잠재적 법적 문제")
    result = st.session_state.task_data["Avaliable_law_issues"]
    
    for i, issue in enumerate(result["potential_legal_issues"]):
        with st.expander(f"문제 {i+1}: {issue['issue_type']}", expanded=True):
            st.markdown(f"""
            <div style="border:1px solid #e0e0e0; border-radius:5px; padding:10px; margin-bottom:10px;">
                <p><strong>문제 부분:</strong> {issue['issue_part']}</p>
                <p><strong>설명:</strong> {issue['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"분석하기", key=f"analyze_button_{i}"):
                    st.session_state.selected_issue = i
                    st.session_state.step = 2
                    st.session_state.analysis_result = None
                    st.session_state.task_data = {k: v for k, v in st.session_state.task_data.items() 
                                                  if k not in ['Law_keyword', 'found_result', 'Related_Laws']}
                    
                    # 기록 추가
                    st.session_state.history.append({
                        "단계": TASKS[st.session_state.step],
                        "선택한 문제": issue['issue_type'],
                        "문제 설명": issue['description']
                    })
                    
                    st.rerun()

def search_laws(_tokenizer, _model):
    messages = st.session_state.task_data["Document_message"]
    try:
        law_keyword, found_result = Search_Laws(_model, _tokenizer, st.session_state.selected_issue, messages)
        st.session_state.task_data['Law_keyword'] = law_keyword
        st.session_state.task_data['found_result'] = found_result
    except Exception as e:
        st.error(f"법률 검색 중 오류가 발생했습니다: {str(e)}")
        st.session_state.task_data['Law_keyword'] = "검색 실패"
        st.session_state.task_data['found_result'] = None


def select_laws(_tokenizer, _model):
    messages = st.session_state.task_data["Document_message"]
    try: 
        st.session_state.task_data['Related_Laws'] = Select_Laws(_model, _tokenizer, st.session_state.selected_issue, messages, st.session_state.task_data['found_result'])
    except Exception as e:
        st.error(f"법률 선택 중 오류가 발생했습니다: {str(e)}")
        st.session_state.task_data['Related_Laws'] = "선택 실패"

def analyze_selected_issue(tokenizer, model):
    issue = st.session_state.task_data["Avaliable_law_issues"]["potential_legal_issues"][st.session_state.selected_issue]
    
    st.markdown("### 선택된 문제")
    st.markdown(f"""
    <div style="border:1px solid #e0e0e0; border-radius:5px; padding:10px; margin-bottom:20px;">
        <h4>{issue['issue_type']}</h4>
        <p><strong>문제 부분:</strong> {issue['issue_part']}</p>
        <p><strong>설명:</strong> {issue['description']}</p>
    </div>
    """, unsafe_allow_html=True)

    # 검색 및 선택 결과가 없거나 선택된 문제가 변경된 경우에만 새로 검색 및 선택 수행
    if ('Law_keyword' not in st.session_state.task_data or 
        'Related_Laws' not in st.session_state.task_data or 
        'last_analyzed_issue' not in st.session_state or 
        st.session_state.last_analyzed_issue != st.session_state.selected_issue):
        
        with st.spinner("관련 법률을 검색 중입니다..."):
            search_laws(tokenizer, model)
            select_laws(tokenizer, model)
        
        # 현재 분석한 문제 저장
        st.session_state.last_analyzed_issue = st.session_state.selected_issue

    st.markdown("### 검색 키워드")
    st.info(st.session_state.task_data['Law_keyword'])
    
    st.markdown("### 관련 법률")
    if st.session_state.task_data['Related_Laws'] != "선택 실패":
        for index, (law, law_id) in enumerate(zip(st.session_state.task_data['Related_Laws']['related_law_list'], 
                                                  st.session_state.task_data['Related_Laws']['related_law_id_list'])):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{law}**")
            with col2:
                if st.button("선택", key=f"select_{law_id}_{index}"):
                    toggle_law_selection(law, law_id)
        
        st.markdown("### 선택된 법률")
        for law in st.session_state.selected_laws:
            st.success(law)
    else:
        st.warning("관련 법률을 찾지 못했습니다.")

    # 선택된 법률 목록이 변경된 경우 세션 상태 업데이트
    if 'last_selected_laws' not in st.session_state or st.session_state.last_selected_laws != st.session_state.selected_laws:
        st.session_state.last_selected_laws = st.session_state.selected_laws.copy()
        # 여기에 선택된 법률 목록이 변경되었을 때 수행할 추가 작업을 넣을 수 있습니다.

def toggle_law_selection(law, law_id):
    if 'selected_laws' not in st.session_state:
        st.session_state.selected_laws = []
        st.session_state.selected_law_ids = []
    
    if law in st.session_state.selected_laws:
        index = st.session_state.selected_laws.index(law)
        st.session_state.selected_laws.pop(index)
        st.session_state.selected_law_ids.pop(index)
    else:
        st.session_state.selected_laws.append(law)
        st.session_state.selected_law_ids.append(law_id)
    
    # 기록 추가
    st.session_state.history.append({
        "단계": TASKS[st.session_state.step],
        "선택/해제된 법률": law,
        "현재 선택된 법률": ", ".join(st.session_state.selected_laws)
    })

def display_law_details(tokenizer, model):
    st.markdown("### 선택된 법률 상세 정보")

    if not st.session_state.selected_laws or not st.session_state.selected_law_ids:
        st.warning("선택된 법률이 없습니다. 이전 단계로 돌아가 법률을 선택해주세요.")
        return

    if 'law_details' not in st.session_state:
        st.session_state.law_details = {}

    for law, law_id in zip(st.session_state.selected_laws, st.session_state.selected_law_ids):
        if law_id not in st.session_state.law_details:
            with st.spinner(f"{law} 상세 정보를 가져오는 중..."):
                try:
                    st.write(f"실행중...")
                    issue = st.session_state.task_data["Avaliable_law_issues"]['potential_legal_issues'][st.session_state.selected_issue]
                    details = search_detail(model, tokenizer, law_id,issue)
                    st.session_state.law_details[law_id] = details
                except Exception as e:
                    st.error(f"{law} 상세 정보를 가져오는 데 실패했습니다: {str(e)}")
                    st.error(f"에러 상세: {traceback.format_exc()}")
                    continue

                if details:
                    st.session_state.law_details[law_id] = details

        st.subheader(law)
        details = st.session_state.law_details.get(law_id)

        if details and 'related_articles' in details and details['related_articles']:
            for article in details['related_articles']:
                with st.expander(f"{article['article_number']}"):
                    st.write(f"**관련 이유:** {article['reason']}")
        else:
            st.write("이 법률에 대한 관련 조항 정보가 없습니다.")

def display_final_summary():
    st.markdown("### 최종 분석 요약")
    
    issue = st.session_state.task_data["Avaliable_law_issues"]['potential_legal_issues'][st.session_state.selected_issue]
    
    st.markdown(f"""
    #### 분석된 법적 문제
    - **문제 유형:** {issue['issue_type']}
    - **문제 부분:** {issue['issue_part']}
    - **설명:** {issue['description']}
    
    #### 관련 법률
    {', '.join(st.session_state.selected_laws)}
    
    #### 주요 관련 조항
    """)
    
    for law_id in st.session_state.selected_law_ids:
        details = st.session_state.law_details.get(law_id)
        if details and 'related_articles' in details:
            for article in details['related_articles']:
                st.markdown(f"- {article['article_number']}: {article['reason']}")

def main():
    st.set_page_config(layout="wide")
    initialize_session_state()
    
    #tokenizer, model = load_model()
    tokenizer,model = 'Using','api'

    display_sidebar()
    display_header()

    if st.session_state.step == 0:
        document_input(tokenizer, model)
    elif st.session_state.step == 1:
        display_potential_issues()
        
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("다시 시작", key="restart"):
                st.session_state.step = 0
                st.session_state.task_data = {}
                st.session_state.selected_issue = None
                st.session_state.analysis_result = None
                st.rerun()
    elif st.session_state.step == 2:
        analyze_selected_issue(tokenizer, model)
        
        col1, col2, col3, col4 = st.columns([1,1,1,1])
        with col2:
            if st.button("다시 생성", key="regenerate"):
                st.session_state.task_data = {k: v for k, v in st.session_state.task_data.items() 
                                              if k not in ['Law_keyword', 'found_result', 'Related_Laws']}
                st.session_state.selected_laws = []
                st.session_state.selected_law_ids = []
                st.cache_data.clear()
                st.rerun()
        with col3:
            if st.button("이전 단계", key="previous_step"):
                st.session_state.step = 1
                st.session_state.task_data = {k: v for k, v in st.session_state.task_data.items() 
                                              if k not in ['Law_keyword', 'found_result', 'Related_Laws']}
                st.session_state.selected_laws = []
                st.session_state.selected_law_ids = []
                st.cache_data.clear()
                st.rerun()
        with col4:
            if st.button("다음 단계", key="next_step"):
                if st.session_state.selected_laws:
                    st.session_state.step = 3
                    st.rerun()
                else:
                    st.warning("다음 단계로 진행하기 전에 최소한 하나의 법률을 선택해주세요.")
    elif st.session_state.step == 3:
        display_law_details(tokenizer, model)
        display_final_summary()
        
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("이전 단계", key="previous_step"):
                st.session_state.step = 2
                # 세션 4에서 세션 3으로 돌아갈 때 관련 상태 초기화
                if 'law_details' in st.session_state:
                    del st.session_state.law_details
                st.rerun()
        with col3:
            if st.button("분석 완료", key="finish_analysis"):
                st.success("분석이 완료되었습니다. 새로운 문서를 분석하려면 '다시 시작'을 클릭하세요.")
                if st.button("다시 시작", key="restart"):
                    st.session_state.step = 1
                    st.session_state.clear()
                    st.rerun()
    # 현재 문서 표시 (모든 단계에서)
    if "document" in st.session_state.task_data:
        with st.expander("현재 분석 중인 문서", expanded=False):
            st.write(st.session_state.task_data["document"])


if __name__ == "__main__":
    main()