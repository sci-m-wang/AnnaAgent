import pandas as pd
from random import choice
from openai import OpenAI
from backbone import model_name, api_key, base_url
import json

events = pd.read_csv('datasets/cbt-triggering-events.csv',header=0)
teen_events = ["在一次重要的考试中表现不佳，比如期末考试、升学考试（如中考或高考），导致自信心受挫。",
               "在学校里被同龄人孤立、嘲笑或遭受言语/身体上的霸凌，感到孤独无助。",
               "父母关系破裂并最终离婚，需要适应新的家庭环境，感到不安或缺乏安全感。",
               "陪伴多年的宠物突然生病或意外去世，第一次直面死亡的悲伤。",
               "因为家庭原因搬到了一个陌生的城市或学校，需要重新适应新环境和结交朋友。",
               "进入青春期后，身体发生明显变化（如长高、变声、月经初潮等），心理上也开始对自我形象产生困惑。",
               "参加一场期待已久的竞赛（如体育比赛、演讲比赛、艺术表演）但未能取得好成绩，感到失落。",
               "与最亲密的朋友发生争执甚至决裂，短时间内难以修复关系，陷入情绪低谷。",
               "家里的经济状况出现问题（如父母失业或生意失败），影响到日常生活，比如不能买喜欢的东西或参与课外活动。",
               "偶然间发现自己特别喜欢某件事情（如画画、编程、音乐、运动），并投入大量时间去练习，逐渐找到自信和成就感。"]

tools = [
    {
        "type": "function",
        "function": {
            'name': 'situationalising_events',
            'description': '根据角色信息和事件，设置一个角色所处的情境。',
            'parameters': {
                "type": "object",
                "properties": {
                    "situation": {
                        "type": "string"
                    }
                },
                "required": ["situation"]
            },
        }
    }
]

def event_trigger(profile):
    age = int(profile['age'])
    if age < 18:
        event = choice(teen_events)
    elif age >= 65:
        event = events[events['Age'] >= 60].sample(1)['Triggering_Event'].values[0]
    else:
        event = events[(events['Age'] >= age-5) & (events['Age'] <= age+5)].sample(1)['Triggering_Event'].values[0]
    return event

def situationalising_events(profile):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 提取患者信息
    patient_info = f"### 患者信息\n年龄：{profile['age']}\n性别：{profile['gender']}"

    event = event_trigger(profile)

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": f"### 任务\n根据患者情况及事件描绘一个患者所处的情境，以第二人称描述。请注意，情境中不要包含患者的个人信息(年龄、性别等)。\n{patient_info}\n### 事件\n{event}"}
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "situationalising_events"}}
    )

    situation = json.loads(response.choices[0].message.tool_calls[0].function.arguments)["situation"]

    return situation


