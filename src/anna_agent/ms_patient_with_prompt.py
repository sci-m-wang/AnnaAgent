'''
AnnaAgent: 具有三级记忆结构的情绪与认知动态的模拟心理障碍患者
1. 首先获取患者的基本信息、病史、症状报告等信息
2. 根据患者的病史、症状报告等信息，生成患者的认知与情绪状态
'''

from .backbone import  get_openai_client
from .common.registry import registry
import os
from .emotion_modulator import emotion_modulation
from .querier import query, is_need
from .complaint_elicitor import switch_complaint, transform_chain




class MsPatient:
    def __init__(self, portrait:dict, report:dict, previous_conversations:list, chain:list, prompt:str):
        self.configuration = {}
        self.portrait = portrait              # age, gender, occupation, maritial_status, symptom
        self.report = report
        self.previous_conversations = previous_conversations
        self.conversation = []          # Conversation存储咨访记录
        self.messages = []              # Messages存储LLM的消息列表
        self.logs = []                 # Logs存储LLM的日志
        self.complaint_chain = chain
        self.system = prompt
        self.chain_index = 1
        self.client = get_openai_client()

    def chat(self, message):
        # 更新消息列表
        self.conversation.append({"role": "Counselor", "content": message})
        self.messages.append({"role": "user", "content": message})
        self.logs.append({"role": "user", "content": message})
        # 初始化本次对话的状态
        emotion = emotion_modulation(self.portrait, self.conversation)
        self.chain_index = switch_complaint(self.complaint_chain, self.chain_index, self.conversation)
        if self.chain_index == -1:
            return "<|end_of_conversation|>"
        complaint = transform_chain(self.complaint_chain)[self.chain_index]
        # 判断是否涉及前疗程内容
        if is_need(message):
            # 生成前疗程内容
            sup_information = query(message, self.previous_conversations, self.report)

            # 生成回复
            response = self.client.chat.completions.create(
                model=registry.get("anna_engine_config").model_name,
                messages=[{"role": "system", "content": self.system}] + self.messages + [{"role": "system", "content": f"当前的情绪状态是：{emotion}，当前的主诉是：{complaint}，涉及到之前疗程的信息是：{sup_information}"}],
            )
            self.logs.append({"role": "assitant", "content": response.choices[0].message.content, "emotion": emotion, "complaint": complaint, "sup_information": sup_information})
        else:
            # 生成回复
            response = self.client.chat.completions.create(
                model=registry.get("anna_engine_config").model_name,
                messages=[{"role": "system", "content": self.system}] + self.messages + [{"role": "system", "content": f"当前的情绪状态是：{emotion}，当前的主诉是：{complaint}"}],
            )
            self.logs.append({"role": "assitant", "content": response.choices[0].message.content, "emotion": emotion, "complaint": complaint})
        # 更新消息列表
        self.conversation.append({"role": "Seeker", "content": response.choices[0].message.content})
        self.messages.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content, emotion, complaint

    def get_system_prompt(self):
        return self.system
    def get_messages(self):
        return self.messages
    def get_logs(self):
        return self.logs
    def get_conversation(self):
        return self.conversation

