from openai import OpenAI
from backbone import api_key, model_name, base_url
import json

tools = [
    {
        "type": "function",
        "function": {
            'name': 'is_recognized',
            'description': '根据对话内容和主诉认知变化链，判断患者目前是否很好地认知到了当前阶段的主诉问题。',
            'parameters': {
                "type": "object",
                "properties": {
                    "is_recognized": {
                        "type": "boolean"
                    },
                }
                },
                "required": ["is_recognized"]
        }
    }
]

def transform_chain(chain):
    transformed_chain = {}
    for node in chain:
        transformed_chain[node["stage"]] = node["content"]
        pass
    return transformed_chain

def switch_complaint(chain, index, conversation):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    transformed_chain = transform_chain(chain)

    print("Transformed chain:", transformed_chain)

    # 提取对话记录
    dialogue_history = "\n".join([f"{conv['role']}: {conv['content']}" for conv in conversation])

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据患者情况及咨访对话历史记录，判断患者当前阶段的主诉问题是否已经得到解决。### 咨访对话历史记录\n{dialogue_history}\n### 主诉认知变化链\n{transformed_chain}\n### 当前阶段\n{transformed_chain[index]}"}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "is_recognized"}}
    )

    if json.loads(response.choices[0].message.tool_calls[0].function.arguments)["is_recognized"]:
        return index+1
    else:
        return index
    