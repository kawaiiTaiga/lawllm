import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np
import random
import time
from utils import *
import re
from search_api import *
from openai import OpenAI
import os
import json

PROMPT = '''You are a helpful AI assistant. Please answer the user's questions kindly. 당신은 유능한 AI 어시스턴트 입니다. 사용자의 질문에 대해 친절하게 답변해주세요.'''


with open('api.json', 'r') as f:
    config = json.load(f)

api_key = config.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def generate_by_openai(prompt):
    response = client.chat.completions.create(messages=prompt, model="gpt-4o", max_tokens=1000)
    return response.choices[0].message.content



def Avaliable_Law_Issue(model, tokenizer, text_data):
    law_issue_json =None
    while law_issue_json == None:
        instruction1 = '당신은 뛰어난 변호사입니다. 문서를 검토하여 혹시 차후에 법적으로 문제가 발생 될 만할 부분을 찾는 작업을 진행합니다. 당신은 아주 조심스럽고 창의적인 변호사이기 때문에, 남들이 생각하지 못한 잠재적인 법적 위험을 감지합니다. \
그 결과는 json의 형태로 저장합니다. \n json 형식 \
{{potential_legal_issues": [{{\n"issue_type": "발생할 수 있는 법적 종류",\n"issue_part" : "본문에서 법적인 문제가 발생할 수 있는 부분", "description": "법적 문제에 대한 설명"}}}},\n 문서 \n {}\n'.format(text_data)
    
        messages = [
        {"role": "system", "content": f"{PROMPT}"},
        {"role": "user", "content": f"{instruction1}"}
        ]
        
        ##Local LLM
        """
        generate_kwargs = {
        "max_new_tokens": 1000,
        "eos_token_id": tokenizer.eos_token_id,}

        law_issue = generate(model,tokenizer,generate_kwargs,messages)
        """
        law_issue = generate_by_openai(messages)
        law_issue_json = extract_json(law_issue)

        messages.append({"role" : "assistant", "content" : law_issue})
    return law_issue_json, messages

def Search_Laws(model,tokenizer,number, messages):
    
    search_result = []

    while not search_result:
        ins2 = f'{number+1}번 케이스에 대한 법에 관련된 내용을 한국법령시스템에 검색하려고 합니다. 이를 위한 키워드 한개를 생성해주세요. 출력 결과는 다음과 같은 형식으로 출력해주세요. [keyword : ]'

        messages.append({"role" : "user", "content" : f"{ins2}"})

        ##Local LLM
        """
        generate_kwargs = {
            "max_new_tokens": 100,
            "eos_token_id": tokenizer.eos_token_id}

        law_keyword = generate(model,tokenizer,generate_kwargs,messages)
        """
        law_keyword = generate_by_openai(messages)
        law_keyword = extract_keyword(law_keyword)
        if law_keyword != None:
            search_result = search_by_keyword(law_keyword)
            
    return law_keyword, search_result


def Select_Laws(model, tokenizer, number, messages, law_list):
    lawlist_text = ','.join([elem['법령명한글'] for elem in law_list])
    ins2 = f'위의 {number+1}번째 케이스는 다음의 법률 리스트 중 어떤 것과 직접적인 관련이 있습니까? 찾아서 작성해주세요. \n법률 리스트 : {lawlist_text}\n json 파일 형식으로 출력해주십시오. {{"related_law_list" : [law1, law2 ..]}} '
    messages.append({"role" : "user", "content" : f"{ins2}"})
    print(messages)
    selected_laws_json = []

    while not selected_laws_json:
        messages.append({"role" : "user", "content" : f"{ins2}"})
        ##Local LLM
        """
        generate_kwargs = {
            "max_new_tokens": 1000,
            "eos_token_id": tokenizer.eos_token_id}

        selected_laws = generate(model, tokenizer, generate_kwargs, messages)
        """
        selected_laws = generate_by_openai(messages)
        selected_laws_json = extract_json(selected_laws)

    # 선택된 법률 이름에 해당하는 ID 찾기
    law_dict = {law['법령명한글']: law['법령ID'] for law in law_list}
    related_law_list = selected_laws_json.get('related_law_list', [])
    related_law_id_list = [law_dict.get(law_name, '') for law_name in related_law_list]

    selected_laws_with_id = {
        'related_law_list': related_law_list,
        'related_law_id_list': related_law_id_list
    }
    print(selected_laws_with_id)
    return selected_laws_with_id

def search_detail(model, tokenizer, law_id, case_data):
    print('dd')
    law_text = search_by_id(law_id)
    case_text =  f'발생할 수 있는 법적 종류 : {case_data["issue_type"]} \n본문에서 법적인 문제가 발생할 수 있는 부분 : {case_data["issue_part"]} \n법적 문제에 대한 설명 : {case_data["description"]}'
    ins2 = f'다음은 어떠한 법의 조문제목들입니다. \n {law_text} \n 다음의 조문들 중에서 다음 케이스와 직접적인 관련이 있는 조문을 찾아주세요. \n {case_text}\n 다음의 json 형태로 출력해주세요. \n {{"related_articles": [{{"article_number" :관련있는 조 번호, "reason" : 관련이 있는 이유 }},]}}'

    messages = [
    {"role": "system", "content": f"{PROMPT}"},
    {"role": "user", "content": f"{ins2}"}
    ]
    
    ##Local LLM
    """
    generate_kwargs = {
            "max_new_tokens": 1000,
            "eos_token_id": tokenizer.eos_token_id}
    
    #generated_text = generate(model, tokenizer, generate_kwargs, messages)
    """
    
    generated_text = generate_by_openai(messages)
    related_articles = extract_json(generated_text)
    print(related_articles)
    return related_articles