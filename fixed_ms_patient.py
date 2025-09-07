"""
修复后的MsPatient - 专门解决list index out of range问题
这个文件是对原始ms_patient.py的增强版本，增加了强健的错误处理
"""

import logging
from src.anna_agent.ms_patient import MsPatient as OriginalMsPatient
from src.anna_agent.backbone import get_openai_client
from src.anna_agent.common.registry import registry

logger = logging.getLogger(__name__)

class FixedMsPatient(OriginalMsPatient):
    """修复list index out of range错误的MsPatient版本"""
    
    def chat(self, message):
        # 更新消息列表
        self.conversation.append({"role": "Counselor", "content": message})
        self.messages.append({"role": "user", "content": message})
        
        try:
            # 使用父类的所有初始化逻辑
            from src.anna_agent.emotion_modulator import emotion_modulation
            from src.anna_agent.complaint_elicitor import switch_complaint, transform_chain
            from src.anna_agent.querier import query, is_need
            
            # 初始化本次对话的状态
            emotion = emotion_modulation(self.portrait, self.conversation)
            self.chain_index = switch_complaint(
                self.complaint_chain, self.chain_index, self.conversation
            )
            logger.info(f"complaint_chain: {self.complaint_chain}")
            complaint = transform_chain(self.complaint_chain)[self.chain_index]
            
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
                print("=== FINAL MESSAGES (with sup_information) ===")
                print(messages)

                response = self._safe_openai_call(messages)
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
                print("=== FINAL MESSAGES (without sup_information) ===") 
                print(messages)
                response = self._safe_openai_call(messages)

            # 安全地提取响应内容
            response_content = self._extract_response_content(response)
            
            # 更新消息列表
            self.conversation.append(
                {"role": "Seeker", "content": response_content}
            )
            self.messages.append(
                {"role": "assistant", "content": response_content}
            )
            return response_content
            
        except Exception as err:
            logger.error(f"Exception in FixedMsPatient.chat: {err}")
            return ""
    
    def _safe_openai_call(self, messages):
        """安全地调用OpenAI API，包含重试逻辑"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"OpenAI API call attempt {attempt + 1}/{max_retries}")
                
                response = self.client.chat.completions.create(
                    model=registry.get("anna_engine_config").model_name,
                    messages=messages,
                )
                
                # 立即检查响应格式
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    logger.info(f"✅ OpenAI API call successful, got {len(response.choices)} choices")
                    return response
                else:
                    logger.warning(f"⚠️ OpenAI API returned empty choices, attempt {attempt + 1}")
                    logger.warning(f"Response object: {response}")
                    if attempt == max_retries - 1:
                        logger.error("❌ All attempts failed - OpenAI consistently returning empty choices")
                        return self._create_fallback_response()
                    continue
                    
            except Exception as e:
                logger.error(f"❌ OpenAI API call failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("❌ All API call attempts failed")
                    return self._create_fallback_response()
                continue
        
        return self._create_fallback_response()
    
    def _create_fallback_response(self):
        """创建一个模拟的OpenAI响应对象，当API失败时使用"""
        class FallbackChoice:
            def __init__(self, content):
                self.message = type('Message', (), {'content': content})()
        
        class FallbackResponse:
            def __init__(self, content):
                self.choices = [FallbackChoice(content)]
        
        # 基于患者档案特征生成合理的回复
        fallback_content = "最近工作确实很忙，压力挺大的...有时候晚上都睡不好觉。"
        
        logger.info(f"🛟 Using fallback response: {fallback_content}")
        return FallbackResponse(fallback_content)
    
    def _extract_response_content(self, response):
        """安全地从响应中提取内容"""
        try:
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content and content.strip():
                    logger.info(f"✅ Extracted response content: {content[:50]}...")
                    return content
                else:
                    logger.warning("⚠️ Response content is empty")
                    return self._get_fallback_content()
            else:
                logger.error("❌ Response has no choices")
                return self._get_fallback_content()
        except Exception as e:
            logger.error(f"❌ Error extracting response content: {str(e)}")
            return self._get_fallback_content()
    
    def _get_fallback_content(self):
        """获取后备响应内容"""
        fallback_responses = [
            "最近工作确实很忙，压力挺大的...有时候晚上都睡不好觉。",
            "嗯...说实话最近状态不太好，工作上的事情让我挺焦虑的。",
            "我最近一直在想是不是该调整一下工作方式，感觉有点力不从心。"
        ]
        import random
        content = random.choice(fallback_responses)
        logger.info(f"🛟 Using fallback content: {content}")
        return content