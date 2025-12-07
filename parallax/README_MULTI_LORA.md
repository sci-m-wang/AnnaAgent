# Parallax 多 LoRA 服务使用指南

## 🎉 好消息!

**Parallax 支持在单个实例中加载多个 LoRA adapters!**

你**不需要**启动多个实例,只需:
1. 启动一个 Parallax 实例
2. 同时注册多个 LoRA adapters
3. 在请求时通过 `model` 参数动态选择使用哪个 LoRA

这比之前的多实例方案**更高效、更节省资源**!

---

## 📦 文件说明

### 推荐方案 (单实例多 LoRA)

- **`start_multi_lora.sh`** - Bash 启动脚本 (单实例)
- **`start_multi_lora.py`** - Python 启动脚本 (单实例,推荐)
- **`client_example.py`** - Python 客户端示例代码

### 备选方案 (多实例,不推荐)

- **`start_multi_models.sh`** - Bash 启动脚本 (多实例)
- **`start_multi_models.py`** - Python 启动脚本 (多实例)

---

## 🚀 快速开始

### 1. 启动服务

```bash
# 使用 Python 脚本 (推荐)
python3 start_multi_lora.py

# 或使用 Bash 脚本
./start_multi_lora.sh
```

### 2. 服务配置

启动后,服务会:
- 加载基础模型: `Qwen/Qwen2.5-7B-Instruct`
- 注册两个 LoRA adapters:
  - `emotion`: 情绪推理模型
  - `chief`: 主诉链路生成模型
- 监听端口: `3000`

### 3. 调用 API

通过 `model` 参数选择使用哪个 LoRA:

```bash
# 使用情绪推理 LoRA
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "emotion",
    "messages": [{"role": "user", "content": "我今天很开心"}],
    "max_tokens": 512
  }'

# 使用主诉链路生成 LoRA
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chief",
    "messages": [{"role": "user", "content": "患者主诉头痛"}],
    "max_tokens": 1024
  }'

# 使用基础模型 (不指定 model)
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 512
  }'
```

---

## 🐍 Python 客户端

### 基础使用

```python
from client_example import ParallaxClient

client = ParallaxClient()

# 情绪推理
result = client.emotion_inference("我今天心情很好")
print(result)

# 主诉链路生成
result = client.chief_chain_generation("患者主诉头痛")
print(result)

# 基础模型
result = client.base_chat("你好")
print(result)
```

### 运行示例代码

```bash
python3 client_example.py
```

示例代码包含:
- ✅ 基础使用
- ✅ 流式输出
- ✅ 多轮对话
- ✅ 批量处理
- ✅ 参数配置
- ✅ 错误处理

---

## 🔧 高级配置

### 添加更多 LoRA

编辑 `start_multi_lora.py`:

```python
LORA_ADAPTERS = {
    "emotion": "sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct",
    "chief": "sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct",
    "your_lora": "your-huggingface-id/your-lora-model",  # 添加新的
}
```

### 调整 LoRA 缓存策略

在启动脚本中修改:

```bash
--max-loras-per-batch 8      # 同一批次最多使用的 LoRA 数量
--max-loaded-loras 8         # 内存中最多加载的 LoRA 数量
--lora-eviction-policy lru   # 淘汰策略: lru 或 fifo
```

### 使用本地 LoRA

如果已下载到本地:

```python
LORA_ADAPTERS = {
    "emotion": "/path/to/local/emotion-lora",
    "chief": "/path/to/local/chief-lora",
}
```

---

## 💡 工作原理

### LoRA 动态加载

```
请求流程:
┌─────────────────────────────────────────┐
│ 客户端请求 (model="emotion")            │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Parallax 检查 LoRA 缓存                 │
│ - 如果已加载: 直接使用                  │
│ - 如果未加载: 从磁盘/HF 加载            │
│ - 如果缓存满: 按 LRU 策略淘汰           │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 基础模型 + emotion LoRA → 推理         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 返回结果                                │
└─────────────────────────────────────────┘
```

### 批处理支持

Parallax 支持在**同一批次**中处理使用**不同 LoRA** 的请求:

```python
# 请求 1: 使用 emotion LoRA
# 请求 2: 使用 chief LoRA
# 请求 3: 不使用 LoRA (基础模型)

# 这三个请求可以在同一批次中处理!
# max-loras-per-batch 控制批次中最多有多少个不同的 LoRA
```

---

## 📊 性能对比

| 方案 | 内存占用 | 启动时间 | 切换延迟 | 资源利用 |
|------|---------|---------|---------|---------|
| **单实例多 LoRA** | ~8GB | ~30s | <100ms | ⭐⭐⭐⭐⭐ |
| 多实例 | ~24GB | ~90s | 0ms | ⭐⭐ |

**推荐使用单实例多 LoRA 方案!**

---

## 🎯 使用场景

### 1. 多专家系统

```python
# 不同任务使用不同的专家模型
emotion_result = client.emotion_inference(text)
chief_result = client.chief_chain_generation(text)
summary_result = client.chat(messages, model="summary")
```

### 2. A/B 测试

```python
# 测试不同版本的 LoRA
result_v1 = client.chat(messages, model="emotion_v1")
result_v2 = client.chat(messages, model="emotion_v2")
```

### 3. 智能路由

```python
# 根据任务类型自动选择模型
def smart_route(task_type, text):
    if task_type == "emotion":
        return client.emotion_inference(text)
    elif task_type == "medical":
        return client.chief_chain_generation(text)
    else:
        return client.base_chat(text)
```

---

## ⚠️ 注意事项

### 内存管理

- 每个 LoRA adapter 占用额外内存 (通常 <500MB)
- `max-loaded-loras` 限制内存中同时加载的 LoRA 数量
- 超过限制时,按 LRU 策略自动卸载

### 首次加载延迟

- 第一次使用某个 LoRA 时需要从磁盘/网络加载
- 后续请求会命中缓存,延迟很低
- 可以预热常用的 LoRA

### 批处理限制

- `max-loras-per-batch` 限制单批次中不同 LoRA 的数量
- 超过限制时,请求会被分到不同批次
- 建议设置为常用 LoRA 数量

---

## 🔍 故障排查

### 1. LoRA 加载失败

```bash
# 检查日志
tail -f parallax_logs/server.log

# 常见原因:
# - LoRA 路径错误
# - 网络问题 (HuggingFace 下载)
# - LoRA 与基础模型不兼容
```

### 2. 内存不足

```bash
# 减少 max-loaded-loras
--max-loaded-loras 4  # 从 8 降到 4

# 或减少批处理大小
--max-batch-size 4  # 从 8 降到 4
```

### 3. 模型未找到

```bash
# 确保请求中的 model 名称与注册的 LoRA 名称一致
# 注册: "emotion=$LORA_EMOTION"
# 请求: "model": "emotion"  ✅
# 请求: "model": "Emotion"  ❌ (大小写敏感)
```

---

## 📚 API 参考

### 请求格式

```json
{
  "model": "emotion",           // LoRA 名称 (可选)
  "messages": [                 // 消息列表
    {"role": "user", "content": "..."}
  ],
  "max_tokens": 512,            // 最大生成 token 数
  "temperature": 0.7,           // 温度参数 (0.0-2.0)
  "top_p": 0.9,                 // nucleus sampling
  "stream": false               // 是否流式输出
}
```

### 响应格式

```json
{
  "id": "req-xxx",
  "object": "chat.completion",
  "model": "emotion",
  "created": 1234567890,
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "..."
    },
    "finish_reason": "eos"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

---

## 📄 许可证

本项目使用 Apache-2.0 许可证。

---

## 🙏 致谢

- [Parallax](https://github.com/GradientHQ/parallax) - 分布式 LLM 推理框架
- [SGLang](https://github.com/sgl-project/sglang) - GPU 后端
- [Qwen](https://huggingface.co/Qwen) - 基础模型

---

**祝使用愉快! 🎉**
