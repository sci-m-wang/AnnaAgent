"""
Parallax 多 LoRA 服务 Python 客户端示例

展示如何调用 Parallax 服务并动态选择不同的 LoRA adapter。
"""

import requests
from typing import Optional, List, Dict, Any


class ParallaxClient:
    """Parallax API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/v1/chat/completions"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表,格式 [{"role": "user", "content": "..."}]
            model: LoRA 模型名称 ("emotion", "chief" 或 None 表示基础模型)
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            stream: 是否流式输出
            **kwargs: 其他参数
        
        Returns:
            API 响应
        """
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            **kwargs
        }
        
        # 只有指定了 model 才添加到 payload
        if model:
            payload["model"] = model
        
        if stream:
            return self._stream_request(payload)
        else:
            response = requests.post(self.endpoint, json=payload)
            response.raise_for_status()
            return response.json()
    
    def _stream_request(self, payload: Dict[str, Any]):
        """处理流式请求"""
        response = requests.post(self.endpoint, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # 去掉 'data: ' 前缀
                    if data == '[DONE]':
                        break
                    yield data
    
    def emotion_inference(self, text: str, **kwargs) -> str:
        """使用情绪推理模型"""
        response = self.chat(
            messages=[{"role": "user", "content": text}],
            model="emotion",
            **kwargs
        )
        return response["choices"][0]["message"]["content"]
    
    def chief_chain_generation(self, text: str, **kwargs) -> str:
        """使用主诉链路生成模型"""
        response = self.chat(
            messages=[{"role": "user", "content": text}],
            model="chief",
            **kwargs
        )
        return response["choices"][0]["message"]["content"]
    
    def base_chat(self, text: str, **kwargs) -> str:
        """使用基础模型"""
        response = self.chat(
            messages=[{"role": "user", "content": text}],
            model=None,  # 不指定 model
            **kwargs
        )
        return response["choices"][0]["message"]["content"]


def example_basic_usage():
    """基础使用示例"""
    print("="*60)
    print("基础使用示例")
    print("="*60)
    
    client = ParallaxClient()
    
    # 1. 情绪推理
    print("\n1. 情绪推理模型:")
    result = client.emotion_inference("我今天心情很好,完成了一个重要项目")
    print(f"输入: 我今天心情很好,完成了一个重要项目")
    print(f"输出: {result}\n")
    
    # 2. 主诉链路生成
    print("2. 主诉链路生成模型:")
    result = client.chief_chain_generation("患者主诉头痛三天,伴有恶心呕吐")
    print(f"输入: 患者主诉头痛三天,伴有恶心呕吐")
    print(f"输出: {result}\n")
    
    # 3. 基础模型
    print("3. 基础模型:")
    result = client.base_chat("你好,请介绍一下你自己")
    print(f"输入: 你好,请介绍一下你自己")
    print(f"输出: {result}\n")


def example_streaming():
    """流式输出示例"""
    print("="*60)
    print("流式输出示例")
    print("="*60)
    
    client = ParallaxClient()
    
    print("\n使用情绪推理模型 (流式):")
    print("输入: 分析这段话的情绪:我今天遇到了很多困难")
    print("输出: ", end="", flush=True)
    
    for chunk in client.chat(
        messages=[{"role": "user", "content": "分析这段话的情绪:我今天遇到了很多困难"}],
        model="emotion",
        stream=True
    ):
        # 解析 JSON 并提取内容
        import json
        try:
            data = json.loads(chunk)
            content = data.get("choices", [{}])[0].get("delta", {}).get("content")
            if content:
                print(content, end="", flush=True)
        except:
            pass
    
    print("\n")


def example_multi_turn_conversation():
    """多轮对话示例"""
    print("="*60)
    print("多轮对话示例")
    print("="*60)
    
    client = ParallaxClient()
    
    # 构建对话历史
    conversation = [
        {"role": "user", "content": "我最近工作压力很大"},
    ]
    
    print("\n用户: 我最近工作压力很大")
    
    # 第一轮
    response = client.chat(messages=conversation, model="emotion")
    assistant_reply = response["choices"][0]["message"]["content"]
    print(f"助手 (情绪推理): {assistant_reply}")
    
    # 添加到对话历史
    conversation.append({"role": "assistant", "content": assistant_reply})
    conversation.append({"role": "user", "content": "有什么建议吗?"})
    
    print("\n用户: 有什么建议吗?")
    
    # 第二轮
    response = client.chat(messages=conversation, model="emotion")
    assistant_reply = response["choices"][0]["message"]["content"]
    print(f"助手 (情绪推理): {assistant_reply}\n")


def example_batch_processing():
    """批量处理示例"""
    print("="*60)
    print("批量处理示例")
    print("="*60)
    
    client = ParallaxClient()
    
    # 批量情绪分析
    texts = [
        "今天天气真好,心情也很愉快",
        "工作太累了,感觉很疲惫",
        "终于完成了这个项目,太开心了",
    ]
    
    print("\n批量情绪分析:")
    for i, text in enumerate(texts, 1):
        result = client.emotion_inference(text, max_tokens=256)
        print(f"{i}. 输入: {text}")
        print(f"   输出: {result}\n")


def example_different_parameters():
    """不同参数示例"""
    print("="*60)
    print("不同参数配置示例")
    print("="*60)
    
    client = ParallaxClient()
    
    text = "分析这段话的情绪"
    
    # 低温度 (更确定性)
    print("\n1. 低温度 (temperature=0.1):")
    result = client.emotion_inference(text, temperature=0.1, max_tokens=100)
    print(f"输出: {result}\n")
    
    # 高温度 (更随机)
    print("2. 高温度 (temperature=1.5):")
    result = client.emotion_inference(text, temperature=1.5, max_tokens=100)
    print(f"输出: {result}\n")


def example_error_handling():
    """错误处理示例"""
    print("="*60)
    print("错误处理示例")
    print("="*60)
    
    client = ParallaxClient()
    
    try:
        # 尝试使用不存在的模型
        result = client.chat(
            messages=[{"role": "user", "content": "测试"}],
            model="nonexistent_model"
        )
        print(f"结果: {result}")
    except requests.exceptions.HTTPError as e:
        print(f"\n捕获到 HTTP 错误: {e}")
        print(f"响应内容: {e.response.text}\n")
    except Exception as e:
        print(f"\n捕获到错误: {e}\n")


if __name__ == "__main__":
    print("\n🎯 Parallax 多 LoRA 服务客户端示例\n")
    
    # 运行所有示例
    try:
        example_basic_usage()
        input("\n按 Enter 继续下一个示例...")
        
        example_streaming()
        input("\n按 Enter 继续下一个示例...")
        
        example_multi_turn_conversation()
        input("\n按 Enter 继续下一个示例...")
        
        example_batch_processing()
        input("\n按 Enter 继续下一个示例...")
        
        example_different_parameters()
        input("\n按 Enter 继续下一个示例...")
        
        example_error_handling()
        
        print("\n✅ 所有示例运行完成!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到 Parallax 服务")
        print("请确保服务已启动: python3 start_multi_lora.py")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
