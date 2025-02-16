from openai import OpenAI
import json
from backbone import api_key, model_name, base_url

tools = [
    {
        "type": "function",
        "function": {
            'name': 'is_need',
            'description': '根据对话内容判断是否涉及之前疗程的内容。',
            'parameters': {
                "type": "object",
                "properties": {
                    "is_need": {
                        "type": "boolean"
                    },
                }
            },
            "required": ["is_need"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "根据对话内容，从知识库中搜索相关的信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "knowledge": {
                        "type": "string"
                    },
                }
            },
            "required": ["knowledge"]
        }
    }
]

def is_need(utterance):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"下面这句话是心理咨询f询师说的话，请判断它是否提及了之前疗程的内容。\n### 话语\n{utterance}"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "is_need"}}
    )

    return json.loads(response.choices[0].message.tool_calls[0].function.arguments)["is_need"]

def query(utterance, conversations, scales):
    # 根据utterance从conversations和scales中检索必要的信息
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据对话内容，从知识库中搜索相关的信息并总结。\n### 对话内容\n{utterance}\n### 知识库\n{conversations}\n{scales}"}
        ],
        tools = tools,
        tool_choice={"type": "function", "function": {"name": "search_knowledge"}}
    )
    knowledge = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["knowledge"]
    return knowledge