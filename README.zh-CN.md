# AnnaAgent

中文说明 | [English](README.md)

本仓库是论文 `AnnaAgent: Dynamic Evolution Agent System with Multi-Session Memory for Realistic Seeker Simulation` 的代码实现。

> **重要仓库更新：** 我们已经删除了此前的 Web 应用相关代码，并将本仓库重构为更纯净的 AnnaAgent 核心工具包，便于读者理解、安装、复现实验和构建下游应用。如果你需要网页应用，请访问已部署站点 [anna.kinamind.org](https://anna.kinamind.org/)，或查看 AnnApod 仓库 [github.com/kinamind/annapod](https://github.com/kinamind/annapod)。

## 声明

由于本研究涉及来自真实心理障碍来访者咨询记录的数据，公开代码只能用于展示部分方法流程。若需要相关数据，请联系[这篇论文](https://aclanthology.org/2022.emnlp-main.156/)的作者。

## 安装

推荐使用 [uv](https://docs.astral.sh/uv/) 在项目本地 `.venv` 中安装依赖：

```bash
uv sync
```

也可以将 AnnaAgent 作为命令行工具安装到独立环境中使用，后续 PyPI 发布后可使用 `uv tool install anna-agent` 或 `pipx install anna-agent`。

## 快速开始

创建一个独立工作区并检查环境：

```bash
uv run anna-agent init anna-workspace
uv run anna-agent doctor --workspace anna-workspace
```

工作区会包含 `settings.yaml`、`.env`、样例案例、提示词状态、运行结果、日志、缓存和资产 manifest。

启动一个样例交互：

```bash
uv run anna-agent demo --workspace anna-workspace
```

运行 `anna-agent` 不带子命令时，会默认读取工作区中的 `interactive.yaml` 并启动交互式对话。

## CLI 使用流程

AnnaAgent 的 CLI 围绕“论文读者从复现实验到实际应用”的完整旅程设计。

### 1. 初始化工作区

```bash
uv run anna-agent init anna-workspace
```

生成的目录结构包括：

```text
anna-workspace/
  settings.yaml
  .env
  assets/
  cases/
  prompts/
  runs/
  outputs/
  logs/
  cache/
```

### 2. 配置模型与服务

可以用交互式向导，也可以用非交互命令修改配置：

```bash
uv run anna-agent config wizard --workspace anna-workspace
uv run anna-agent config set model_service.base_url https://example.com/v1 \
  --workspace anna-workspace
uv run anna-agent config show --workspace anna-workspace
uv run anna-agent config validate --workspace anna-workspace
```

API key 等敏感信息建议写入 `.env`，不要提交到 Git。

### 3. 下载论文资产

资产下载由 `assets/anna-assets.json` 管理。默认 `paper` preset 指向已发布的 HuggingFace SFT 模型和合成数据：

```bash
uv run anna-agent assets list --workspace anna-workspace
uv run anna-agent assets pull paper --workspace anna-workspace
```

默认资产包括：

- 情绪推断 SFT 模型：`sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct`
- 主诉链生成 SFT 模型：`sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct`
- 合成标准数据：`sci-m-wang/Anna-CPsyCounD`

你也可以编辑 `assets/anna-assets.json`，加入自己的 HuggingFace 仓库或直接下载 URL。

### 4. 数据准备与校验

运行实验前建议先校验案例格式：

```bash
uv run anna-agent data validate anna-workspace/cases/family_stress_case.json
uv run anna-agent data inspect anna-workspace/cases/family_stress_case.json
uv run anna-agent data sample --out anna-workspace/cases/sample.json
```

案例文件主要包含：

- `portrait`：来访者画像、风险分数和症状
- `report`：结构化咨询案例报告
- `conversation` 或 `previous_conversations`：前一疗程对话历史

### 5. 连通性测试

正式运行昂贵实验前，建议单独测试模型、embedding 和记忆库：

```bash
uv run anna-agent test embedding --workspace anna-workspace
uv run anna-agent test memory --workspace anna-workspace
uv run anna-agent test model --workspace anna-workspace
uv run anna-agent test all --workspace anna-workspace
```

### 6. 长期记忆

AnnaAgent 使用 LanceDB 存储本地长期记忆。前疗程对话和报告会被切分为：

- `conversation_turn`
- `conversation_window`
- `session_summary`
- `report_section`
- `report_summary`

索引样例案例：

```bash
uv run anna-agent memory index anna-workspace/cases/family_stress_case.json \
  --workspace anna-workspace
```

检索长期记忆：

```bash
uv run anna-agent memory search "胸闷和家庭压力" \
  --workspace anna-workspace \
  --seeker-id 42289a5f-bbdc-43f9-826a-9569bbbd5feb
```

查看或重置记忆库：

```bash
uv run anna-agent memory stats --workspace anna-workspace
uv run anna-agent memory inspect --workspace anna-workspace
uv run anna-agent memory reset --workspace anna-workspace --yes
```

默认记忆数据写入 `.anna_memory/`，该目录已被 Git 忽略。

### 7. Embedding 配置

embedding 层会优先调用配置的 OpenAI-compatible embedding 服务；如果服务不可用，会自动回退到确定性的本地 hash embedding。

`.env` 中可以使用 AnnaAgent 命名或常见 OpenAI 风格别名：

```bash
ANNA_ENGINE_EMBEDDING_API_KEY=...
ANNA_ENGINE_EMBEDDING_BASE_URL=https://your-embedding-endpoint/v1
ANNA_ENGINE_EMBEDDING_MODEL_NAME=your-embedding-model

# 也支持：
OPENAI_EMBEDDING_API_KEY=...
OPENAI_EMBEDDING_BASE_URL=https://your-embedding-endpoint/v1
OPENAI_EMBEDDING_MODEL=your-embedding-model
```

### 8. 初始化 AnnaAgent

初始化可以运行完整流程，也可以只生成 prompt-only state，用于低成本 dry-run 或固定初始化 prompt。

```bash
uv run anna-agent initialize prompt-only anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.prompt.json

uv run anna-agent initialize full anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.full.json \
  --workspace anna-workspace

uv run anna-agent initialize freeze anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.frozen.json \
  --workspace anna-workspace

uv run anna-agent initialize from-prompt anna-workspace/prompts/family.prompt.json
```

### 9. 交互式对话

可以从案例文件启动，也可以从固定 prompt state 启动：

```bash
uv run anna-agent chat --workspace anna-workspace \
  --case anna-workspace/cases/family_stress_case.json \
  --save anna-workspace/runs/manual-chat.jsonl

uv run anna-agent chat --workspace anna-workspace \
  --state anna-workspace/prompts/family.prompt.json
```

### 10. 批量实验

默认批量运行只生成初始化状态，不调用模型；添加 `--live` 后会执行脚本化对话。

```bash
uv run anna-agent run batch --workspace anna-workspace \
  --case 'cases/*.json' \
  --out anna-workspace/runs/batch

uv run anna-agent run batch --workspace anna-workspace \
  --case 'cases/*.json' \
  --script scripts/counselor_messages.json \
  --live \
  --out anna-workspace/runs/live-batch
```

### 11. 启动接口服务

可以启动一个轻量 JSON API 服务，供外部实验驱动或应用调用：

```bash
uv run anna-agent serve --workspace anna-workspace --host 127.0.0.1 --port 8000
```

当前服务包含：

- `GET /health`
- `GET /v1/sessions`
- `POST /v1/sessions`
- `POST /v1/chat`
- `POST /v1/memory/search`

### 12. 日志、缓存与清理

```bash
uv run anna-agent logs tail anna-workspace/logs/anna-agent.log
uv run anna-agent cache list --workspace anna-workspace
uv run anna-agent cache clean --workspace anna-workspace --yes
uv run anna-agent reset workspace --workspace anna-workspace --yes
uv run anna-agent doctor --workspace anna-workspace
```

## 使用基础模型替代 SFT 模型

情绪推断器和主诉链生成器默认设计为调用训练后的 SFT 模型。如果暂时没有部署 SFT checkpoint，可以在 `settings.yaml` 中关闭对应模块的 SFT 开关，让模块回退到 `model_service` 中配置的基础模型：

```yaml
model_service:
  model_name: counselor
  api_key: counselor
  base_url: http://localhost:8002/v1
servers:
  complaint:
    use_sft_model: false
  emotion:
    use_sft_model: false
```

也可以使用环境变量：

```bash
ANNA_ENGINE_COMPLAINT_USE_SFT_MODEL=false
ANNA_ENGINE_EMOTION_USE_SFT_MODEL=false
```

## 样例案例

仓库提供了家庭压力样例：`docs/family_stress_case.json`。

- `id`：`42289a5f-bbdc-43f9-826a-9569bbbd5feb`
- `conversation`：作为长期记忆的前疗程对话历史
- `report`：结构化咨询报告
- `portrait`：来访者画像和症状

运行一次完整单轮示例：

```bash
uv sync
uv run python -m anna_agent.initialize
rm -f interactive.yaml
cp docs/family_stress_case.json interactive.json
printf "最近一次感到伤心或者失望的时候，是什么原因导致的？\nexit\n" | \
  ANNA_ENGINE_COMPLAINT_USE_SFT_MODEL=false \
  ANNA_ENGINE_EMOTION_USE_SFT_MODEL=false \
  uv run anna-agent
```

## 方法概览

为便于读者理解 AnnaAgent 的工作流程，我们提供了下图：

![](https://github.com/sci-m-wang/AnnaAgent/blob/main/src/anna_agent/figure/whiteboard_exported_image_en.png)

AnnaAgent 通过两组 agent 模块模拟来访者：

- **动态演化模块**：包含情绪调节器、主诉链生成器和主诉切换器。
- **多疗程记忆模块**：包含情境分析、状态分析和记忆检索。

系统主要分为两个阶段：

- **初始化阶段**：读取来访者基本画像、历史疗程对话和报告；分析说话风格；基于画像和报告总结历史量表；匹配近期事件并生成当前情境；完成当前量表并分析状态变化；生成主诉链。
- **对话阶段**：咨询师每次发言后，记忆检索器判断是否需要检索长期记忆；情绪调节器推理下一步情绪并根据上下文扰动情绪；主诉切换器判断是否进入下一个主诉阶段。

## 模型

情绪推断器和主诉链生成器的训练数据来自真实数据。由于伦理风险，我们不会开源带标注的原始数据。为促进后续研究与应用，我们将模型设置为有条件公开。

| 模型 | 链接 | Backbone |
| --- | --- | --- |
| 情绪推断器 | [link](https://huggingface.co/sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct) | Qwen2.5-7B-Instruct |
| 主诉链生成器 | [link](https://huggingface.co/sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct) | Qwen2.5-7B-Instruct |

我们会继续基于更多架构训练和发布新的情绪推断器与主诉链生成器。

## 合成数据

我们使用 [CPsyCounD](https://github.com/CAS-SIAT-XinHai/CPsyCoun) 数据集作为种子，通过 GPT-4o-mini 合成了符合 AnnaAgent 格式要求的 seeker bank。数据可在 [HuggingFace](https://huggingface.co/datasets/sci-m-wang/Anna-CPsyCounD) 获取。后续我们会继续转换更多数据，并基于 AnnaAgent 创建更真实的来访者角色。

## 开发者指南

- [开发者指南（中文）](src/docs/contributing/code.md)
- [Developer Guide（English）](src/docs/contributing/code_en.md)

## 引用

```bibtex
@inproceedings{wang-etal-2025-annaagent,
    title = "{A}nna{A}gent: Dynamic Evolution Agent System with Multi-Session Memory for Realistic Seeker Simulation",
    author = "Wang, Ming  and
      Wang, Peidong  and
      Wu, Lin  and
      Yang, Xiaocui  and
      Wang, Daling  and
      Feng, Shi  and
      Chen, Yuxin  and
      Wang, Bixuan  and
      Zhang, Yifei",
    editor = "Che, Wanxiang  and
      Nabende, Joyce  and
      Shutova, Ekaterina  and
      Pilehvar, Mohammad Taher",
    booktitle = "Findings of the Association for Computational Linguistics: ACL 2025",
    month = jul,
    year = "2025",
    address = "Vienna, Austria",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2025.findings-acl.1192/",
    doi = "10.18653/v1/2025.findings-acl.1192",
    pages = "23221--23235",
    ISBN = "979-8-89176-256-5",
    abstract = "Constrained by the cost and ethical concerns of involving real seekers in AI-driven mental health, researchers develop LLM-based conversational agents (CAs) with tailored configurations, such as profiles, symptoms, and scenarios, to simulate seekers. While these efforts advance AI in mental health, achieving more realistic seeker simulation remains hindered by two key challenges: dynamic evolution and multi-session memory. Seekers' mental states often fluctuate during counseling, which typically spans multiple sessions. To address this, we propose **AnnaAgent**, an emotional and cognitive dynamic agent system equipped with tertiary memory. AnnaAgent incorporates an emotion modulator and a complaint elicitor trained on real counseling dialogues, enabling dynamic control of the simulator{'}s configurations. Additionally, its tertiary memory mechanism effectively integrates short-term and long-term memory across sessions. Evaluation results, both automated and manual, demonstrate that AnnaAgent achieves more realistic seeker simulation in psychological counseling compared to existing baselines. The ethically reviewed and screened code can be found on [https://github.com/sci-m-wang/AnnaAgent](https://github.com/sci-m-wang/AnnaAgent)."
}
```
