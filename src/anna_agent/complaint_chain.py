from .backbone import get_complaint_client
from .event_trigger import event_trigger
import json


tools = [
    {
        "type": "function",
        "function": {
            "name": "generate_complaint_chain",
            "description": "根据角色信息和近期遭遇的事件，生成一个患者的主诉请求认知变化链",
            "parameters": {
                "type": "object",
                "properties": {
                    "chain": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"stage": {"type": "integer"}, "content": {"type": "string"}},
                            "additionalProperties": False,
                            "required": ["stage", "content"],
                        },
                        "minItems": 3,
                        "maxItems": 7,
                    }
                },
                "required": ["chain"],
            },
        },
    }
]

model_name = "complaint"


def gen_complaint_chain(profile):
    patient_info = f"### 患者信息\n年龄：{profile['age']}\n性别：{profile['gender']}\n职业：{profile['occupation']}\n婚姻状况：{profile['martial_status']}\n症状：{profile['symptoms']}"
    event = event_trigger(profile)
    client = get_complaint_client()
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": f"### 任务\n根据患者情况及近期遭遇事件生成患者的主诉认知变化链。请注意，事件可能与患者信息冲突，如果发生这种情况，以患者的信息为准。\n{patient_info}\n### 近期遭遇事件\n{event}",
            }
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "generate_complaint_chain"}},
    )
    chain = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["chain"]
    return chain
