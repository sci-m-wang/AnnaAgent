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
    messages = [
        {
            "role": "user",
            "content": (
                "请判断下面这句咨询师的发言是否包含了对之前疗程或历史对话的提及。\n\n"
                "【任务说明】\n"
                "判断标准包括但不限于：是否提到了过去的咨询记录、曾讨论过的话题、上次谈话的内容，或者使用了‘你上次说过’、‘我们之前谈到’等引用性表达。\n\n"
                "【咨询师发言】\n"
                f"{utterance}\n\n"
                "请返回判断结果（是 / 否）以及判断依据。"
            )
        }
    ]

    print(messages)
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
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
