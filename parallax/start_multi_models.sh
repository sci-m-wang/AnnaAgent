#!/bin/bash
# Parallax 多模型启动脚本
# 
# 说明:
# - Parallax 不支持在单个实例中同时运行多个模型
# - 此脚本启动三个独立的 Parallax 实例,每个使用不同端口
# - 前两个模型使用 LoRA adapter,基于 Qwen2.5-7B-Instruct

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Parallax 多模型服务启动脚本 ===${NC}"

# 配置
BASE_MODEL="Qwen/Qwen2.5-7B-Instruct"
LORA_EMOTION="sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct"
LORA_CHIEF="sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct"

# 端口配置
PORT_EMOTION=3000
PORT_CHIEF=3001
PORT_BASE=3002

# 日志目录
LOG_DIR="./parallax_logs"
mkdir -p "$LOG_DIR"

# PID 文件目录
PID_DIR="./parallax_pids"
mkdir -p "$PID_DIR"

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止所有 Parallax 实例...${NC}"
    
    if [ -f "$PID_DIR/emotion.pid" ]; then
        kill $(cat "$PID_DIR/emotion.pid") 2>/dev/null || true
        rm "$PID_DIR/emotion.pid"
    fi
    
    if [ -f "$PID_DIR/chief.pid" ]; then
        kill $(cat "$PID_DIR/chief.pid") 2>/dev/null || true
        rm "$PID_DIR/chief.pid"
    fi
    
    if [ -f "$PID_DIR/base.pid" ]; then
        kill $(cat "$PID_DIR/base.pid") 2>/dev/null || true
        rm "$PID_DIR/base.pid"
    fi
    
    echo -e "${GREEN}所有实例已停止${NC}"
    exit 0
}

# 捕获 Ctrl+C
trap cleanup SIGINT SIGTERM

# 启动情绪推理模型 (LoRA)
echo -e "\n${GREEN}[1/3] 启动情绪推理模型服务...${NC}"
echo -e "  - 模型: $LORA_EMOTION"
echo -e "  - 端口: $PORT_EMOTION"
echo -e "  - 日志: $LOG_DIR/emotion.log"

python3 ./src/parallax/launch.py \
    --model-path "$BASE_MODEL" \
    --port $PORT_EMOTION \
    --host 0.0.0.0 \
    --max-batch-size 8 \
    --enable-lora \
    --lora-paths "emotion=$LORA_EMOTION" \
    --max-loras-per-batch 1 \
    --log-level INFO \
    > "$LOG_DIR/emotion.log" 2>&1 &

echo $! > "$PID_DIR/emotion.pid"
echo -e "${GREEN}✓ 情绪推理模型已启动 (PID: $(cat $PID_DIR/emotion.pid))${NC}"

# 等待服务启动
sleep 5

# 启动主诉链路生成模型 (LoRA)
echo -e "\n${GREEN}[2/3] 启动主诉链路生成模型服务...${NC}"
echo -e "  - 模型: $LORA_CHIEF"
echo -e "  - 端口: $PORT_CHIEF"
echo -e "  - 日志: $LOG_DIR/chief.log"

python3 ./src/parallax/launch.py \
    --model-path "$BASE_MODEL" \
    --port $PORT_CHIEF \
    --host 0.0.0.0 \
    --max-batch-size 8 \
    --enable-lora \
    --lora-paths "chief=$LORA_CHIEF" \
    --max-loras-per-batch 1 \
    --log-level INFO \
    > "$LOG_DIR/chief.log" 2>&1 &

echo $! > "$PID_DIR/chief.pid"
echo -e "${GREEN}✓ 主诉链路生成模型已启动 (PID: $(cat $PID_DIR/chief.pid))${NC}"

# 等待服务启动
sleep 5

# 启动基础模型
echo -e "\n${GREEN}[3/3] 启动基础 Qwen2.5-7B-Instruct 模型服务...${NC}"
echo -e "  - 模型: $BASE_MODEL"
echo -e "  - 端口: $PORT_BASE"
echo -e "  - 日志: $LOG_DIR/base.log"

python3 ./src/parallax/launch.py \
    --model-path "$BASE_MODEL" \
    --port $PORT_BASE \
    --host 0.0.0.0 \
    --max-batch-size 8 \
    --log-level INFO \
    > "$LOG_DIR/base.log" 2>&1 &

echo $! > "$PID_DIR/base.pid"
echo -e "${GREEN}✓ 基础模型已启动 (PID: $(cat $PID_DIR/base.pid))${NC}"

# 显示服务信息
echo -e "\n${GREEN}=== 所有服务已启动 ===${NC}"
echo -e "\n${YELLOW}服务端点:${NC}"
echo -e "  1. 情绪推理模型:      http://localhost:$PORT_EMOTION/v1/chat/completions"
echo -e "  2. 主诉链路生成模型:  http://localhost:$PORT_CHIEF/v1/chat/completions"
echo -e "  3. 基础模型:          http://localhost:$PORT_BASE/v1/chat/completions"

echo -e "\n${YELLOW}日志文件:${NC}"
echo -e "  1. $LOG_DIR/emotion.log"
echo -e "  2. $LOG_DIR/chief.log"
echo -e "  3. $LOG_DIR/base.log"

echo -e "\n${YELLOW}测试命令示例:${NC}"
cat << 'EOF'

# 测试情绪推理模型
curl -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "emotion",
    "messages": [{"role": "user", "content": "我今天很开心"}],
    "stream": false
  }'

# 测试主诉链路生成模型
curl -X POST http://localhost:3001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chief",
    "messages": [{"role": "user", "content": "患者主诉头痛"}],
    "stream": false
  }'

# 测试基础模型
curl -X POST http://localhost:3002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'

EOF

echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}\n"

# 保持脚本运行
wait
