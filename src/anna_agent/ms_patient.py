from .backbone import get_counselor_client, get_openai_client
from .common.registry import registry
from .fill_scales import fill_scales, fill_scales_previous
from .event_trigger import event_trigger, situationalising_events
from .emotion_modulator import emotion_modulation
from .querier import query, is_need
from .complaint_elicitor import switch_complaint, transform_chain
from .complaint_chain import gen_complaint_chain
from .short_term_memory import summarize_scale_changes
from .style_analyzer import analyze_style
import random
import logging
from .anna_agent_template import prompt_template

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 控制台打印
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

logger.addHandler(handler)


class MsPatient:
    def __init__(self, portrait: dict, report: dict, previous_conversations: list):
        self.configuration = {}
        self.portrait = portrait  # age, gender, occupation, maritial_status, symptom
        # self.profile = {key:self.portrait[key] for key in self.portrait if key != "symptom"}          # profile不包含症状symptom
        self.configuration["gender"] = self.portrait["gender"]
        self.configuration["age"] = self.portrait["age"]
        self.configuration["occupation"] = self.portrait["occupation"]
        self.configuration["marriage"] = self.portrait["martial_status"]
        self.report = report
        self.previous_conversations = previous_conversations
        # 填写之前疗程的量表
        self.p_bdi, self.p_ghq, self.p_sass = fill_scales_previous(
            self.portrait, self.report
        )
        self.conversation = []  # Conversation存储咨访记录
        self.messages = []  # Messages存储LLM的消息列表
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
        self.configuration[
            "status"
        ] = ""  # 先置状态为空，后续会根据量表分析结果进行更新
        seeker_utterances = [
            utterance["content"]
            for utterance in self.previous_conversations
            if utterance["role"] == "Seeker"
        ]
        # 兼容空的历史会话，避免 random.choices 在空列表上触发"list index out of range"
        if seeker_utterances:
            k = 3 if len(seeker_utterances) >= 3 else len(seeker_utterances)
            self.configuration["statement"] = random.choices(seeker_utterances, k=k)
        else:
            # 提供一个合理的默认主述，保证下游 Prompt 渲染不失败
            self.configuration["statement"] = ["最近工作压力有点大，睡眠也不太好。"]
        # 填写当前量表
        # bdi = ["B","B","B","B","B","B","B","B","B","B","B","B","B","B","B","B","B","B","B","B","B"]
        # ghq = ["C","C","B","B","D","C","B","C","B","B","D","B","C","B","D","B","C","B","D","B","C","B","B","B","D","B","B","B"]
        # sass = ["B","B","C","B","C","B","B","B","B","B","C","B","C","B","C","B","B","B","B","B","B"]
        # self.bdi, self.ghq, self.sass = bdi, ghq, sass

        self.bdi, self.ghq, self.sass = fill_scales(
            prompt_template.format(**self.configuration)
        )
        scales = {
            "p_bdi": self.p_bdi,
            "p_ghq": self.p_ghq,
            "p_sass": self.p_sass,
            "bdi": self.bdi,
            "ghq": self.ghq,
            "sass": self.sass,
        }
        # 分析近期状态
        self.status = summarize_scale_changes(scales)
        self.configuration["status"] = self.status
        # 选取对话样例
        self.system = prompt_template.format(**self.configuration)
        self.chain_index = 1
        self.client = get_openai_client()

    def chat(self, message):
        # 更新消息列表
        self.conversation.append({"role": "Counselor", "content": message})
        self.messages.append({"role": "user", "content": message})
        try:
            # 初始化本次对话的状态
            emotion = emotion_modulation(self.portrait, self.conversation)
            self.chain_index = switch_complaint(
                self.complaint_chain, self.chain_index, self.conversation
            )
            logger.info(f"complaint_chain: {self.complaint_chain}")
            # 安全地获取complaint，避免list index out of range错误
            transformed_chain = transform_chain(self.complaint_chain)
            if transformed_chain and len(transformed_chain) > self.chain_index:
                complaint = transformed_chain[self.chain_index]
            else:
                logger.warning(
                    f"chain_index {self.chain_index} 超出范围，使用默认complaint"
                )
                complaint = "工作焦虑，失眠问题"
            # 判断是否涉及前疗程内容
            if is_need(message):
                # 生成前疗程内容
                sup_information = query(
                    message, self.previous_conversations, self.report
                )

                # 生成回复
                messages = (
                    [{"role": "system", "content": self.system}]
                    + self.messages
                    + [
                        {
                            "role": "user",
                            "content": f"当前的情绪状态是：{emotion}，当前的主诉是：{complaint}，涉及到之前疗程的信息是：{sup_information}",
                        }
                    ]
                )
                print(messages)

                response = self.client.chat.completions.create(
                    model=registry.get("anna_engine_config").model_name,
                    messages=messages,
                )
            else:
                # 生成回复
                messages = (
                    [{"role": "system", "content": self.system}]
                    + self.messages
                    + [
                        {
                            "role": "user",
                            "content": f"当前的情绪状态是：{emotion}，当前的主诉是：{complaint}",
                        }
                    ]
                )
                print(messages)
                response = self.client.chat.completions.create(
                    model=registry.get("anna_engine_config").model_name,
                    messages=messages,
                )

            # 更新消息列表
            # 安全地提取响应内容，避免list index out of range错误
            if response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
            else:
                logger.warning("OpenAI API返回空的choices数组，使用默认响应")
                response_content = (
                    "抱歉，我刚才走神了...最近工作太忙，脑子有点乱。你刚才说什么？"
                )

            self.conversation.append({"role": "Seeker", "content": response_content})
            self.messages.append({"role": "assistant", "content": response_content})
            return response_content
        except Exception as err:
            logger.error("Exception", err)

            return ""
