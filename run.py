from ms_patient import MsPatient
import json

if __name__ == "__main__":
    # 模拟患者信息 (非真实数据)
    # 这里的患者信息是虚构的，仅用于演示目的
    portrait = {
        "drisk": 3,
        "srisk": 2,
        "age": "42",
        "gender": "女",
        "martial_status": "离婚",
        "occupation": "教师",
        "symptoms": "缺乏自信心，自我价值感低，有自罪感，无望感；体重剧烈增加；精神运动性激越；有自杀想法"
    }
    report = {
        "案例标题": "决断困难与自罪感的焦虑障碍案例",
        "案例类别": [
        "焦虑障碍",
        "自我价值感低落"
        ],
        "运用的技术": [
        "认知行为疗法",
        "情感支持"
        ],
        "案例简述": [
        "患者为58岁已婚女性，报告缺乏自信心及决断困难，伴随精神运动性迟滞和自我价值感低落。患者自述有自罪感和无望感，并有自残倾向。虽然与朋友的社交没有明显隔阂，但其情绪低落和不安感影响了日常生活。"
        ],
        "咨询经过": [
        "患者在初次面谈中表达了对自我能力的严重怀疑，认为自己拖累了他人。询问后得知，患者近期没有明显的生活事件作为诱因，但长期以来一直感到行动迟缓，脑海中常有空白。尽管对饮食和睡眠的描述正常，患者仍不时产生自残冲动。患者表示，朋友在关键时刻提供了支持，避免了自残行为的发生。",
        "在对话过程中，医生观察到患者容易焦躁，尽管头晕症状不存在。医生建议患者通过与朋友交流和外出活动来舒缓情绪压力。在此基础上，患者被鼓励探索内心深处的情感根源，以改善自我价值感。"
        ],
        "经验感想": [
        "本案例显示出患者的低自我价值感和决断困难与其内心深处的焦虑情绪有直接关联。患者的情绪波动虽然没有具体的生活事件作为诱因，但可能与长期的心理压力和未解决的自我怀疑有关。建议患者通过认知行为疗法重新审视自我认知，增强自我价值感，并通过情感支持系统稳定情绪波动。",
        "治疗过程中，患者意识到朋友的支持在缓解情绪危机中的重要性，这为其提供了一个积极的情感出口。未来的治疗可以进一步加强患者的自我认知和情感管理能力，帮助其建立更积极的自我形象与生活态度。"
        ]
    }
    previous_conversations = [
        {
            "role": "Seeker",
            "content": "医生你好"
        },
        {
            "role": "Counselor",
            "content": "你好。有什么想聊聊吗"
        },
        {
            "role": "Seeker",
            "content": "我感觉人生很失败，什么事情都干不好，还经常拖累别人"
        },
        {
            "role": "Counselor",
            "content": "您这样想的原因是什么呢。最近发生什么事情了吗"
        },
        {
            "role": "Seeker",
            "content": "我感觉最近自己行动变得很拖沓，事情做不好就会很急躁。而且有的时候大脑一片空白"
        },
        {
            "role": "Counselor",
            "content": "好的。没有什么原因吗。那这种情况持续多久了呢"
        },
        {
            "role": "Seeker",
            "content": "我也不知道是什么原因。有一阵子了"
        },
        {
            "role": "Counselor",
            "content": "好吧。有没有对以前喜欢的事情不感兴趣呢"
        },
        {
            "role": "Seeker",
            "content": "没有"
        },
        {
            "role": "Counselor",
            "content": "吃饭还好吗"
        },
        {
            "role": "Seeker",
            "content": "一切正常"
        },
        {
            "role": "Counselor",
            "content": "不错哦。那睡觉呢"
        },
        {
            "role": "Seeker",
            "content": "也还好。尽管如此。我还是时不时有自残的冲动"
        },
        {
            "role": "Counselor",
            "content": "和朋友社交怎么样呢。有没有隔阂感"
        },
        {
            "role": "Seeker",
            "content": "没有。也正是因为他们才及时阻止了我"
        },
        {
            "role": "Counselor",
            "content": "好的。那有没有感到头晕 容易焦虑呢。（刚有事 回的有点慢 不好意思）"
        },
        {
            "role": "Seeker",
            "content": "确实容易焦躁。头晕的话没事"
        },
        {
            "role": "Counselor",
            "content": "ok。你的情况我基本了解了。虽然你不愿意说你难过的原因。但是不用有太大压力。无论发生什么都要尽量乐观点。平常可以多和朋友聊聊。多去走走 可以放轻松。那今天就到这里啦"
        }
    ]

    seeker = MsPatient(portrait, report, previous_conversations)
    # 模拟对话
    while True:
        message = input("请输入您的消息: ")
        if message.lower() == "exit":
            break
        try:
            response = seeker.chat(message)
        except Exception as err:
            print("Error:", err)
            continue
        print("Counselor:", message)
        print("Seeker:", response)