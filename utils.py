import xml.etree.ElementTree as ET
import json
import re
def get_content(element):
    content = ""
    if element.tag == "조문내용":
        content += element.text.strip() if element.text else ""
    for child in element:
        if child.tag in ["항", "호", "목"]:
            content += get_content(child)
        elif child.tag in ["항내용", "호내용", "목내용"]:
            content += child.text.strip() if child.text else ""
    return content

def search_and_store(xml_string, keyword):
    root = ET.fromstring(xml_string)
    
    results = {}
    
    for jonum in root.findall(".//조문단위"):
        jo_number = jonum.find("조문번호").text if jonum.find("조문번호") is not None else None
        
        content = get_content(jonum)
        
        if keyword in content:
            results[jo_number] = {
                'content': content,
                'structure': {}
            }
            
            # 키워드 검색 및 구조 저장
            if keyword in jonum.find("조문내용").text:
                results[jo_number]['structure']["조문"] = True
            
            for i, hang in enumerate(jonum.findall(".//항"), 1):
                hang_content = hang.find("항내용")
                if hang_content is not None and hang_content.text and keyword in hang_content.text:
                    results[jo_number]['structure'][f"{i}항"] = {"내용": True}
                
                for j, ho in enumerate(hang.findall(".//호"), 1):
                    ho_content = ho.find("호내용")
                    if ho_content is not None and ho_content.text and keyword in ho_content.text:
                        if f"{i}항" not in results[jo_number]['structure']:
                            results[jo_number]['structure'][f"{i}항"] = {}
                        results[jo_number]['structure'][f"{i}항"][f"{j}호"] = True
                    
                    for k, mok in enumerate(ho.findall(".//목"), 1):
                        mok_content = mok.find("목내용")
                        if mok_content is not None and mok_content.text and keyword in mok_content.text:
                            if f"{i}항" not in results[jo_number]['structure']:
                                results[jo_number]['structure'][f"{i}항"] = {}
                            if f"{j}호" not in results[jo_number]['structure'][f"{i}항"]:
                                results[jo_number]['structure'][f"{i}항"][f"{j}호"] = []
                            results[jo_number]['structure'][f"{i}항"][f"{j}호"].append(f"{k}목")
    
    return results

def extract_json(text):
    # JSON 부분을 정규표현식으로 찾습니다
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group()
        # JSON 문자열을 파이썬 객체로 변환합니다
        try:
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            print("JSON 파싱 중 오류가 발생했습니다.")
            return None
    else:
        print("텍스트에서 JSON을 찾을 수 없습니다.")
        return None

def extract_keyword(text):
    pattern = r'\[keyword\s*:\s*(.*?)\]'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    else:
        return None