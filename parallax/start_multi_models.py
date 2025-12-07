#!/usr/bin/env python3
"""
Parallax 多模型启动脚本 (Python 版本)

此脚本启动三个独立的 Parallax 实例:
1. 情绪推理模型 (LoRA adapter)
2. 主诉链路生成模型 (LoRA adapter)
3. 基础 Qwen2.5-7B-Instruct 模型

每个模型运行在不同的端口上,提供独立的 API 服务。
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# 配置
CONFIG = {
    "emotion": {
        "name": "情绪推理模型",
        "base_model": "Qwen/Qwen2.5-7B-Instruct",
        "lora_adapter": "sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct",
        "port": 3000,
        "model_name": "emotion",
    },
    "chief": {
        "name": "主诉链路生成模型",
        "base_model": "Qwen/Qwen2.5-7B-Instruct",
        "lora_adapter": "sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct",
        "port": 3001,
        "model_name": "chief",
    },
    "base": {
        "name": "基础模型",
        "base_model": "Qwen/Qwen2.5-7B-Instruct",
        "lora_adapter": None,
        "port": 3002,
        "model_name": "qwen2.5-7b",
    },
}

# 全局进程列表
processes = []
log_dir = Path("./parallax_logs")
log_dir.mkdir(exist_ok=True)


def cleanup(signum=None, frame=None):
    """清理所有子进程"""
    print("\n\n🛑 正在停止所有 Parallax 实例...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        except Exception as e:
            print(f"⚠️  停止进程时出错: {e}")
    
    print("✅ 所有实例已停止")
    sys.exit(0)


def start_service(service_id: str, config: dict):
    """启动单个 Parallax 服务"""
    print(f"\n{'='*60}")
    print(f"🚀 启动 {config['name']}")
    print(f"{'='*60}")
    print(f"  模型名称: {config['model_name']}")
    print(f"  基础模型: {config['base_model']}")
    if config['lora_adapter']:
        print(f"  LoRA 适配器: {config['lora_adapter']}")
    print(f"  端口: {config['port']}")
    
    # 构建命令
    cmd = [
        "python3",
        "./src/parallax/launch.py",
        "--model-path", config['base_model'],
        "--port", str(config['port']),
        "--host", "0.0.0.0",
        "--max-batch-size", "8",
        "--log-level", "INFO",
    ]
    
    # 添加 LoRA 参数
    if config['lora_adapter']:
        cmd.extend([
            "--enable-lora",
            "--lora-paths", f"{config['model_name']}={config['lora_adapter']}",
            "--max-loras-per-batch", "1",
        ])
    
    # 启动进程
    log_file = log_dir / f"{service_id}.log"
    print(f"  日志文件: {log_file}")
    
    with open(log_file, "w") as f:
        proc = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
        )
    
    processes.append(proc)
    print(f"✅ {config['name']} 已启动 (PID: {proc.pid})")
    
    # 等待服务启动
    print(f"⏳ 等待服务初始化...")
    time.sleep(8)
    
    return proc


def print_summary():
    """打印服务摘要信息"""
    print("\n" + "="*60)
    print("✅ 所有服务已成功启动")
    print("="*60)
    
    print("\n📡 API 端点:")
    for service_id, config in CONFIG.items():
        print(f"  {config['name']:20s} → http://localhost:{config['port']}/v1/chat/completions")
    
    print("\n📝 日志文件:")
    for service_id in CONFIG.keys():
        print(f"  {service_id:10s} → {log_dir}/{service_id}.log")
    
    print("\n🧪 测试命令示例:")
    print("""
# 测试情绪推理模型
curl -X POST http://localhost:3000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "emotion",
    "messages": [{"role": "user", "content": "我今天很开心"}],
    "stream": false
  }'

# 测试主诉链路生成模型
curl -X POST http://localhost:3001/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "chief",
    "messages": [{"role": "user", "content": "患者主诉头痛"}],
    "stream": false
  }'

# 测试基础模型
curl -X POST http://localhost:3002/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
""")
    
    print("\n💡 提示:")
    print("  - 使用 Ctrl+C 停止所有服务")
    print("  - 查看日志: tail -f parallax_logs/*.log")
    print("  - 检查进程: ps aux | grep parallax")
    print()


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("🎯 Parallax 多模型服务启动器")
    print("="*60)
    
    # 检查是否在正确的目录
    if not Path("./src/parallax/launch.py").exists():
        print("❌ 错误: 请在 parallax 项目根目录下运行此脚本")
        sys.exit(1)
    
    # 启动所有服务
    for service_id, config in CONFIG.items():
        try:
            start_service(service_id, config)
        except Exception as e:
            print(f"❌ 启动 {config['name']} 失败: {e}")
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
            for proc in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️  检测到进程 {proc.pid} 已退出")
                    cleanup()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
