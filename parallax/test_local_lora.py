#!/usr/bin/env python3
"""
Parallax 单实例多 LoRA 测试脚本 (修复版 - 单节点部署)
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# 配置 - 使用本地路径
BASE_MODEL = "/root/models/Qwen/Qwen2.5-7B-Instruct"
LORA_ADAPTERS = {
    "emotion": "/root/models/sci-m-wang/Emotion_Inferencer-adapter-Qwen2.5_7B_Instruct",
}
PORT = 3000
NUM_LAYERS = 28  # Qwen2.5-7B-Instruct 有 28 层

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
    print("🚀 启动 Parallax 服务 (单节点多 LoRA)")
    print("="*60)
    print(f"  基础模型: {BASE_MODEL}")
    print(f"  模型层数: {NUM_LAYERS}")
    print(f"  LoRA Adapters:")
    for name, path in LORA_ADAPTERS.items():
        print(f"    - {name}: {path}")
    print(f"  端口: {PORT}")
    
    # 检查模型路径
    if not Path(BASE_MODEL).exists():
        print(f"❌ 错误: 基础模型路径不存在: {BASE_MODEL}")
        sys.exit(1)
    
    for name, path in LORA_ADAPTERS.items():
        if not Path(path).exists():
            print(f"❌ 错误: LoRA 路径不存在: {path}")
            sys.exit(1)
    
    # 构建 LoRA paths 参数
    lora_paths = [f"{name}={path}" for name, path in LORA_ADAPTERS.items()]
    
    # 构建命令 - 添加层范围参数
    cmd = [
        "python3",
        "./src/parallax/launch.py",
        "--model-path", BASE_MODEL,
        "--port", str(PORT),
        "--host", "0.0.0.0",
        "--start-layer", "0",           # 从第 0 层开始
        "--end-layer", str(NUM_LAYERS),  # 到第 28 层结束
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
    print(f"\n📝 启动命令:")
    print(f"  {' '.join(cmd)}\n")
    
    with open(log_file, "w") as f:
        process = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd(),
        )
    
    print(f"✅ Parallax 服务已启动 (PID: {process.pid})")
    
    # 等待服务启动
    print(f"⏳ 等待服务初始化 (这可能需要 60-90 秒,模型加载中)...")
    
    # 监控日志
    for i in range(90):
        time.sleep(1)
        
        # 检查进程是否还在运行
        if process.poll() is not None:
            print(f"\n❌ 进程意外退出!")
            print(f"\n📋 最后 50 行日志:")
            os.system(f"tail -50 {log_file}")
            sys.exit(1)
        
        # 每 10 秒显示一次进度
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}s")
    
    return process


def test_service():
    """测试服务是否正常"""
    import requests
    
    print("\n" + "="*60)
    print("🧪 测试服务")
    print("="*60)
    
    # 测试基础模型
    print("\n1. 测试基础模型 (不使用 LoRA):")
    try:
        response = requests.post(
            f"http://localhost:{PORT}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "你好,请用一句话介绍你自己"}],
                "max_tokens": 50,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ 成功!")
        content = result['choices'][0]['message']['content']
        print(f"   响应: {content[:100]}...")
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 emotion LoRA
    print("\n2. 测试 emotion LoRA:")
    try:
        response = requests.post(
            f"http://localhost:{PORT}/v1/chat/completions",
            json={
                "model": "emotion",
                "messages": [{"role": "user", "content": "我今天很开心"}],
                "max_tokens": 50,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ 成功!")
        content = result['choices'][0]['message']['content']
        print(f"   响应: {content[:100]}...")
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()


def print_summary():
    """打印服务摘要信息"""
    print("\n" + "="*60)
    print("✅ 服务测试完成")
    print("="*60)
    
    print(f"\n📡 API 端点:")
    print(f"  http://localhost:{PORT}/v1/chat/completions")
    
    print(f"\n🎯 可用的模型:")
    for name in LORA_ADAPTERS.keys():
        print(f"  - {name}")
    print(f"  - (不指定 model 参数则使用基础模型)")
    
    print(f"\n📝 日志文件:")
    print(f"  {log_dir}/server.log")
    
    print("\n💡 提示:")
    print("  - 使用 Ctrl+C 停止服务")
    print("  - 查看日志: tail -f parallax_logs/server.log")
    print()


def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("🎯 Parallax 单节点多 LoRA 测试脚本 (修复版)")
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
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
    
    # 测试服务
    try:
        test_service()
    except Exception as e:
        print(f"⚠️  测试失败: {e}")
        print("💡 服务可能还在启动中,请稍后手动测试")
        import traceback
        traceback.print_exc()
    
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
