#!/usr/bin/env python3
"""
Parallax 单实例多 LoRA 启动脚本

此脚本启动一个 Parallax 实例,同时加载多个 LoRA adapters:
1. 情绪推理模型 (LoRA adapter)
2. 主诉链路生成模型 (LoRA adapter)
3. 基础 Qwen2.5-7B-Instruct 模型

在请求时通过 "model" 参数动态选择使用哪个 LoRA。
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# 配置
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
LORA_ADAPTERS = {
    "emotion": "sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct",
    "chief": "sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct",
}
PORT = 3000

# 全局进程
process = None
log_dir = Path("./parallax_logs")
log_dir.mkdir(exist_ok=True)


def cleanup(signum=None, frame=None):
    """清理进程"""
    global process
    print("\n\n🛑 正在停止 Parallax 服务...")
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except Exception as e:
            print(f"⚠️  停止进程时出错: {e}")
    
    print("✅ 服务已停止")
    sys.exit(0)


def start_service():
    """启动 Parallax 服务"""
    global process
    
    print("="*60)
    print("🚀 启动 Parallax 服务 (单实例多 LoRA)")
    print("="*60)
    print(f"  基础模型: {BASE_MODEL}")
    print(f"  LoRA Adapters:")
    for name, path in LORA_ADAPTERS.items():
        print(f"    - {name}: {path}")
    print(f"  端口: {PORT}")
    
    # 构建 LoRA paths 参数
    lora_paths = [f"{name}={path}" for name, path in LORA_ADAPTERS.items()]
    
    # 构建命令
    cmd = [
        "python3",
        "./src/parallax/launch.py",
        "--model-path", BASE_MODEL,
        "--port", str(PORT),
        "--host", "0.0.0.0",
        "--max-batch-size", "8",
        "--enable-lora",
        "--lora-paths", *lora_paths,
        "--max-loras-per-batch", "8",
        "--max-loaded-loras", "8",
        "--lora-eviction-policy", "lru",
        "--log-level", "INFO",
    ]
    
    # 启动进程
    log_file = log_dir / "server.log"
    print(f"  日志文件: {log_file}")
    
    with open(log_file, "w") as f:
        process = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
        )
    
    print(f"✅ Parallax 服务已启动 (PID: {process.pid})")
    
    # 等待服务启动
    print(f"⏳ 等待服务初始化...")
    time.sleep(10)
    
    return process


def print_summary():
    """打印服务摘要信息"""
    print("\n" + "="*60)
    print("✅ 服务已就绪")
    print("="*60)
    
    print(f"\n📡 API 端点:")
    print(f"  http://localhost:{PORT}/v1/chat/completions")
    
    print(f"\n🎯 可用的模型 (通过 'model' 参数选择):")
    for name in LORA_ADAPTERS.keys():
        print(f"  - {name}")
    print(f"  - (不指定 model 参数则使用基础模型)")
    
    print(f"\n📝 日志文件:")
    print(f"  {log_dir}/server.log")
    
    print("\n🧪 测试命令示例:")
    print("""
# 1. 使用情绪推理 LoRA
curl -X POST http://localhost:3000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "emotion",
    "messages": [{"role": "user", "content": "我今天很开心"}],
    "max_tokens": 512,
    "stream": false
  }'

# 2. 使用主诉链路生成 LoRA
curl -X POST http://localhost:3000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "chief",
    "messages": [{"role": "user", "content": "患者主诉头痛"}],
    "max_tokens": 1024,
    "stream": false
  }'

# 3. 使用基础模型
curl -X POST http://localhost:3000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
""")
    
    print("\n💡 提示:")
    print("  - 使用 Ctrl+C 停止服务")
    print("  - 查看日志: tail -f parallax_logs/server.log")
    print("  - LoRA 会根据 LRU 策略自动加载/卸载")
    print("  - 同一批次最多可以使用 8 个不同的 LoRA")
    print()


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("🎯 Parallax 单实例多 LoRA 服务启动器")
    print("="*60)
    
    # 检查是否在正确的目录
    if not Path("./src/parallax/launch.py").exists():
        print("❌ 错误: 请在 parallax 项目根目录下运行此脚本")
        sys.exit(1)
    
    # 启动服务
    try:
        start_service()
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
        cleanup()
        sys.exit(1)
    
    # 打印摘要
    print_summary()
    
    # 保持运行
    print("🔄 服务运行中... (按 Ctrl+C 停止)")
    try:
        while True:
            time.sleep(1)
            # 检查进程是否还在运行
            if process.poll() is not None:
                print(f"\n⚠️  检测到进程 {process.pid} 已退出")
                print("💡 查看日志: tail -f parallax_logs/server.log")
                cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
