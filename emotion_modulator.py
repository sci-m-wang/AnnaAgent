from openai import OpenAI
from random import randint
from emotion_pertuber import perturb_state
import json

tools = [
    {
        "type": "function",
        "function": {
            'name': 'emotion_inference',
            'description': '根据profile和对话记录，推理下一句情绪',
            'parameters': {
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string",
                        "enum": [
                            "admiration", "amusement", "anger", "annoyance", "approval", "caring",
                            "confusion", "curiosity", "desire", "disappointment", "disapproval",
                            "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
                            "joy", "love", "nervousness", "optimism", "pride", "realization",
                            "relief", "remorse", "sadness", "surprise", "neutral"
                        ],
                        "description": "推理出的情绪类别，必须是GoEmotions定义的27种情绪之一。"
                    }
                },
                "required": ["emotion"]
            },
        }
    }
]

model_name = "emotion"

# 根据profile和dialogue推测emotion
def emotion_inferencer(profile, conversation):
    client = OpenAI(
        api_key="emotion_inferencer",
        base_url="http://0.0.0.0:8000/v1/",
    )

    # 提取患者信息
    patient_info = f"### 患者信息\n年龄：{profile['age']}\n性别：{profile['gender']}\n职业：{profile['occupation']}\n婚姻状况：{profile['martial_status']}\n症状：{profile['symptoms']}"
    
    # 提取对话记录
    dialogue_history = "\n".join([f"{conv['role']}: {conv['content']}" for conv in conversation])

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据患者情况及咨访对话历史记录推测患者下一句话最可能的情绪。\n{patient_info}\n### 对话记录\n{dialogue_history}"}
        ],
        # functions=[tools[0]["function"]],
        # function_call={"name": "emotion_inference"}
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "emotion_inference"}}
    )
    # print(response)

    emotion = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["emotion"]

    return emotion

def emotion_modulation(profile, conversation):
    indicator = randint(0,100)
    emotion = emotion_inferencer(profile,conversation)
    # print(emotion)
    if indicator > 90:
        return perturb_state(emotion)
    else:
        return emotion
