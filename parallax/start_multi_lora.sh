#!/bin/bash
# Parallax 单实例多 LoRA 启动脚本
# 
# 说明:
# - 只启动一个 Parallax 实例,加载一个基础模型
# - 同时注册多个 LoRA adapters
# - 在请求时通过 "model" 参数动态选择使用哪个 LoRA

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Parallax 单实例多 LoRA 服务启动脚本 ===${NC}"

# 配置
BASE_MODEL="Qwen/Qwen2.5-7B-Instruct"
LORA_EMOTION="sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct"
LORA_CHIEF="sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct"

# 服务端口
PORT=3000

# 日志目录
LOG_DIR="./parallax_logs"
mkdir -p "$LOG_DIR"

# PID 文件
PID_FILE="./parallax.pid"

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止 Parallax 服务...${NC}"
    
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null || true
        rm "$PID_FILE"
    fi
    
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

# 捕获 Ctrl+C
trap cleanup SIGINT SIGTERM

# 启动服务
echo -e "\n${GREEN}启动 Parallax 服务 (单实例多 LoRA)${NC}"
echo -e "  - 基础模型: $BASE_MODEL"
echo -e "  - LoRA Adapters:"
echo -e "    1. emotion: $LORA_EMOTION"
echo -e "    2. chief: $LORA_CHIEF"
echo -e "  - 端口: $PORT"
echo -e "  - 日志: $LOG_DIR/server.log"

python3 ./src/parallax/launch.py \
    --model-path "$BASE_MODEL" \
    --port $PORT \
    --host 0.0.0.0 \
    --max-batch-size 8 \
    --enable-lora \
    --lora-paths \
        "emotion=$LORA_EMOTION" \
        "chief=$LORA_CHIEF" \
    --max-loras-per-batch 8 \
    --max-loaded-loras 8 \
    --lora-eviction-policy lru \
    --log-level INFO \
    > "$LOG_DIR/server.log" 2>&1 &

echo $! > "$PID_FILE"
echo -e "${GREEN}✓ Parallax 服务已启动 (PID: $(cat $PID_FILE))${NC}"

# 等待服务启动
echo -e "\n${YELLOW}等待服务初始化...${NC}"
sleep 10

# 显示服务信息
echo -e "\n${GREEN}=== 服务已就绪 ===${NC}"
echo -e "\n${YELLOW}API 端点:${NC}"
echo -e "  http://localhost:$PORT/v1/chat/completions"

echo -e "\n${YELLOW}可用的模型 (通过 'model' 参数选择):${NC}"
echo -e "  1. emotion      - 情绪推理模型"
echo -e "  2. chief        - 主诉链路生成模型"
echo -e "  3. (不指定)     - 基础 Qwen2.5-7B-Instruct 模型"

echo -e "\n${YELLOW}日志文件:${NC}"
echo -e "  $LOG_DIR/server.log"

echo -e "\n${YELLOW}测试命令示例:${NC}"
cat << 'EOF'

# 1. 使用情绪推理 LoRA
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "emotion",
    "messages": [{"role": "user", "content": "我今天很开心"}],
    "max_tokens": 512,
    "stream": false
  }'

# 2. 使用主诉链路生成 LoRA
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chief",
    "messages": [{"role": "user", "content": "患者主诉头痛"}],
    "max_tokens": 1024,
    "stream": false
  }'

# 3. 使用基础模型 (不指定 model 或 model="default")
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 512,
    "stream": false
  }'

# 4. 流式输出示例
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "emotion",
    "messages": [{"role": "user", "content": "分析这段话的情绪"}],
    "stream": true
  }'

EOF

echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}\n"

# 保持脚本运行
wait
