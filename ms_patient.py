from openai import OpenAI
from backbone import api_key, model_name, base_url
from fill_scales import fill_scales, fill_scales_previous
from event_trigger import event_trigger, situationalising_events
from emotion_modulator import emotion_modulation
from querier import query, is_need
from complaint_elicitor import switch_complaint, transform_chain
from complaint_chain import gen_complaint_chain
from short_term_memory import summarize_scale_changes
from style_analyzer import analyze_style
import random
from anna_agent_template import prompt_template

class MsPatient:
    def __init__(self, portrait:dict, report:dict, previous_conversations:list):
        self.configuration = {}
        self.portrait = portrait              # age, gender, occupation, maritial_status, symptom
        # self.profile = {key:self.portrait[key] for key in self.portrait if key != "symptom"}          # profile不包含症状symptom
        self.configuration["gender"] = self.portrait["gender"]
        self.configuration["age"] = self.portrait["age"]
        self.configuration["occupation"] = self.portrait["occupation"]
        self.configuration["marriage"] = self.portrait["martial_status"]
        self.report = report
        self.previous_conversations = previous_conversations
        # 填写之前疗程的量表
        self.p_bdi, self.p_ghq, self.p_sass = fill_scales_previous(self.portrait, self.report)
        self.conversation = []          # Conversation存储咨访记录
        self.messages = []              # Messages存储LLM的消息列表
        # 生成主诉认知变化链
        self.complaint_chain = gen_complaint_chain(self.portrait)
        # 生成近期事件
        self.event = event_trigger(self.portrait)
        # 总结短期记忆-事件
        self.situation = situationalising_events(self.portrait)
        self.configuration["situation"] = self.situation
        # 分析说话风格
        self.style = analyze_style(self.portrait, self.previous_conversations)
        self.configuration["style"] = self.style
        self.configuration["status"] = ""  # 先置状态为空，后续会根据量表分析结果进行更新
        seeker_utterances = [utterance["content"] for utterance in self.previous_conversations if utterance["role"] == "Seeker"]
        self.configuration["statement"] = random.choices(seeker_utterances,k=3)
        # 填写当前量表
        self.bdi, self.ghq, self.sass = fill_scales(prompt_template.format(**self.configuration))
        scales = {
            "p_bdi": self.p_bdi,
            "p_ghq": self.p_ghq,
            "p_sass": self.p_sass,
            "bdi": self.bdi,
            "ghq": self.ghq,
            "sass": self.sass
        }
        # 分析近期状态
        self.status = summarize_scale_changes(scales)
        self.configuration["status"] = self.status
        # 选取对话样例
        self.system = prompt_template.format(**self.configuration)
        self.chain_index = 1
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def chat(self, message):
        # 更新消息列表
        self.conversation.append({"role": "Counselor", "content": message})
        self.messages.append({"role": "user", "content": message})
        # 初始化本次对话的状态
        emotion = emotion_modulation(self.portrait, self.conversation)
        self.chain_index = switch_complaint(self.complaint_chain, self.chain_index, self.conversation)
        complaint = transform_chain(self.complaint_chain)[self.chain_index]
        # 判断是否涉及前疗程内容
        if is_need(message):
            # 生成前疗程内容
            sup_information = query(message, self.previous_conversations, self.report)
            
            # 生成回复
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": self.system}] + self.messages + [{"role": "system", "content": f"当前的情绪状态是：{emotion}，当前的主诉是：{complaint}，涉及到之前疗程的信息是：{sup_information}"}],
            )
        else:
            # 生成回复
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": self.system}] + self.messages + [{"role": "system", "content": f"当前的情绪状态是：{emotion}，当前的主诉是：{complaint}"}],
            )
        # 更新消息列表
        self.conversation.append({"role": "Seeker", "content": response.choices[0].message.content})
        self.messages.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content

