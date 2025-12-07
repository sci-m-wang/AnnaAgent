# Parallax 多模型服务使用说明

## 概述

此项目包含两个启动脚本,用于同时运行三个独立的 Parallax 模型服务:

1. **情绪推理模型** (端口 3000) - 使用 LoRA adapter
2. **主诉链路生成模型** (端口 3001) - 使用 LoRA adapter  
3. **基础 Qwen2.5-7B-Instruct** (端口 3002) - 无 adapter

## 重要说明

⚠️ **Parallax 限制**: Parallax 目前不支持在单个实例中同时运行多个不同的模型。因此,这些脚本会启动**三个独立的 Parallax 实例**,每个运行在不同的端口上。

## 使用方法

### 方式一: Bash 脚本 (推荐 Linux/macOS)

```bash
# 赋予执行权限
chmod +x start_multi_models.sh

# 启动所有服务
./start_multi_models.sh
```

### 方式二: Python 脚本 (跨平台)

```bash
# 直接运行
python3 start_multi_models.py

# 或者赋予执行权限后运行
chmod +x start_multi_models.py
./start_multi_models.py
```

## API 调用示例

### 1. 情绪推理模型

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "emotion",
    "messages": [
      {"role": "user", "content": "我今天很开心,因为完成了一个重要项目"}
    ],
    "max_tokens": 512,
    "temperature": 0.7,
    "stream": false
  }'
```

### 2. 主诉链路生成模型

```bash
curl -X POST http://localhost:3001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chief",
    "messages": [
      {"role": "user", "content": "患者主诉:头痛三天,伴有恶心"}
    ],
    "max_tokens": 1024,
    "temperature": 0.7,
    "stream": false
  }'
```

### 3. 基础模型

```bash
curl -X POST http://localhost:3002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好,请介绍一下你自己"}
    ],
    "max_tokens": 512,
    "stream": false
  }'
```

## 流式输出示例

```bash
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "emotion",
    "messages": [{"role": "user", "content": "分析这段话的情绪"}],
    "stream": true
  }'
```

## Python 客户端示例

```python
import requests

def call_emotion_model(text: str):
    """调用情绪推理模型"""
    response = requests.post(
        "http://localhost:3000/v1/chat/completions",
        json={
            "model": "emotion",
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 512,
            "temperature": 0.7,
        }
    )
    return response.json()

def call_chief_model(text: str):
    """调用主诉链路生成模型"""
    response = requests.post(
        "http://localhost:3001/v1/chat/completions",
        json={
            "model": "chief",
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 1024,
        }
    )
    return response.json()

def call_base_model(text: str):
    """调用基础模型"""
    response = requests.post(
        "http://localhost:3002/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": text}],
            "max_tokens": 512,
        }
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 情绪分析
    result = call_emotion_model("我今天心情不太好")
    print("情绪分析:", result)
    
    # 主诉链路生成
    result = call_chief_model("患者主诉头痛")
    print("主诉链路:", result)
    
    # 基础对话
    result = call_base_model("你好")
    print("基础对话:", result)
```

## 日志查看

所有日志文件保存在 `parallax_logs/` 目录:

```bash
# 实时查看所有日志
tail -f parallax_logs/*.log

# 查看特定模型日志
tail -f parallax_logs/emotion.log
tail -f parallax_logs/chief.log
tail -f parallax_logs/base.log
```

## 停止服务

- **Bash 脚本**: 按 `Ctrl+C`
- **Python 脚本**: 按 `Ctrl+C`

脚本会自动清理所有子进程。

## 手动管理

如果脚本异常退出,可以手动清理:

```bash
# 查找进程
ps aux | grep parallax

# 杀死进程
kill <PID>

# 或者杀死所有 parallax 进程
pkill -f "parallax/launch.py"
```

## 配置修改

### 修改端口

编辑脚本中的 `CONFIG` 部分:

```python
CONFIG = {
    "emotion": {
        "port": 3000,  # 修改为你想要的端口
        ...
    },
    ...
}
```

### 修改模型路径

如果你已经下载了模型到本地:

```python
CONFIG = {
    "emotion": {
        "base_model": "/path/to/local/Qwen2.5-7B-Instruct",
        "lora_adapter": "/path/to/local/Emotion_inferencer",
        ...
    },
}
```

### 调整批处理大小

```bash
# 在脚本中修改
--max-batch-size 16  # 默认是 8
```

## 性能优化建议

1. **GPU 内存**: 三个模型会占用大量 GPU 内存,建议至少 24GB VRAM
2. **批处理**: 根据你的硬件调整 `--max-batch-size`
3. **并发**: 如果内存不足,可以只启动需要的模型
4. **量化**: 考虑使用量化版本的基础模型

## 故障排查

### 端口被占用

```bash
# 检查端口占用
lsof -i :3000
lsof -i :3001
lsof -i :3002

# 杀死占用端口的进程
kill -9 <PID>
```

### 内存不足

- 减少 `--max-batch-size`
- 只启动必要的模型
- 使用量化模型

### 模型下载失败

- 检查网络连接
- 使用 HuggingFace 镜像站
- 预先下载模型到本地

## 注意事项

1. ⚠️ 确保有足够的 GPU 内存 (推荐 3x8GB = 24GB+)
2. ⚠️ 首次运行会自动下载模型,需要时间和网络
3. ⚠️ 每个模型独立运行,无法共享 KV cache
4. ⚠️ 这不是最优的资源利用方式,但是 Parallax 的限制

## 替代方案

如果你需要更高效的多模型服务,考虑:

- **vLLM**: 支持 LoRA 多路复用
- **SGLang**: 原生支持多 LoRA adapter
- **OpenAI-compatible 代理**: 在单个端点后面路由到不同模型
