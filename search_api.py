import requests
import xml.etree.ElementTree as ET
import json

with open('api.json', 'r') as f:
    config = json.load(f)

api_key = config.get("LEGAL_API_KEY")

# API 엔드포인트 URL
url = "http://law.go.kr/DRF/lawSearch.do"

def search_by_keyword(keyword):
    
    # 기본 요청 파라미터
    base_params = {
        "OC": api_key,
        "target": "law",
        "type": "XML",
        "query": keyword,
        "search": 2
    }

    result = []

    # 300201과 300202에 대해 각각 요청
    for rrClsCd in ['300201', '300202']:
        params = base_params.copy()
        params['rrClsCd'] = rrClsCd

        # GET 요청 보내기
        response = requests.get(url, params=params)

        # 응답 상태 확인
        if response.status_code == 200:
            # XML 파싱
            root = ET.fromstring(response.content)

            # 파싱된 데이터 처리
            for law in root.findall('.//law'):
                law_id = law.find('법령ID').text
                law_name = law.find('법령명한글').text
                result.append({'법령ID': law_id, '법령명한글': law_name})
        else:
            print(f"Error for rrClsCd {rrClsCd}: {response.status_code}")
    
    return result


def extract_articles(xml_string):
    root = ET.fromstring(xml_string)
    articles = []

    for jonum in root.findall(".//조문단위"):
        jo_number = jonum.find("조문번호")
        jo_title = jonum.find("조문제목")
        jo_content = jonum.find('조문내용')

        if jo_number is not None and jo_title is not None:
            articles.append({
                "조번호": jo_number.text.strip(),
                "조문제목": jo_title.text.strip(),
                "조문내용" : jo_content.text.strip()
            })

    return articles


def search_by_id(id):
    url = "http://law.go.kr/DRF/lawService.do"

    # 요청 파라미터
    params = {
        "OC": api_key,
        "target": "law",
        "type": "XML",
        "ID" : f'{id}'
    }

    # GET 요청 보내기
    response = requests.get(url, params=params)
    xml_string = response.text
    result = extract_articles(xml_string)