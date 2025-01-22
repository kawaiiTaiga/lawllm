# 문서 법률 자문 시스템 (Legal Document Advisory System)

이 프로젝트는 OpenAI의 Language Model을 활용하여 법률 문서를 분석하고 관련 법률 정보를 제공하는 웹 애플리케이션입니다.

## 주요 기능

- 법률 문서 분석
- 잠재적 법적 위험요소 식별
- 관련 법률 검색 및 추천
- 법조항 상세 정보 제공

## 시스템 요구사항

- Python 3.8 이상
- 필요한 API 키:
  - OpenAI API 키
  - 국가법령정보센터 API 키

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. API 키 설정
- 프로젝트 루트 디렉토리에 `api.json` 파일 생성
- 아래 형식으로 API 키 정보 입력:
```json
{
    "openai_api_key": "your-openai-api-key",
    "law_api_key": "your-law-api-key"
}
```

## 실행 방법

```bash
streamlit run main.py
```

## 사용 방법

1. **문서 입력**
   - 분석이 필요한 법률 문서를 텍스트 영역에 입력
   - "검토 시작" 버튼 클릭

2. **법적 위험요소 확인**
   - 시스템이 식별한 잠재적 법적 문제 확인
   - 관심 있는 문제 선택하여 상세 분석 진행

3. **관련 법률 검토**
   - 시스템이 추천하는 관련 법률 확인
   - 관련성 높은 법률 선택

4. **상세 정보 확인**
   - 선택한 법률의 관련 조항 확인
   - 적용 근거 검토

## 사용 기술

- OpenAI API
- Streamlit
- 국가법령정보센터 API

## 주의사항

- 이 시스템은 법률 전문가의 조언을 완전히 대체할 수 없습니다.
- 참고용 도구로만 사용하시기 바랍니다.
- 실제 법률 자문이 필요한 경우 반드시 법률 전문가와 상담하세요.

