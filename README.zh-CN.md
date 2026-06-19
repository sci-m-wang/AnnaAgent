# AnnaAgent

中文说明 | [English](README.md)

本仓库是论文 `AnnaAgent: Dynamic Evolution Agent System with Multi-Session Memory for Realistic Seeker Simulation` 的代码实现。

> **重要仓库更新：** 我们已经删除了此前的 Web 应用相关代码，并将本仓库重构为更纯净的 AnnaAgent 核心工具包，便于读者理解、安装、复现实验和构建下游应用。如果你需要网页应用，请访问已部署站点 [anna.kinamind.org](https://anna.kinamind.org/)，或查看 AnnApod 仓库 [github.com/kinamind/annapod](https://github.com/kinamind/annapod)。

## 声明

由于本研究涉及来自真实心理障碍来访者咨询记录的数据，公开代码只能用于展示部分方法流程。若需要相关数据，请联系[这篇论文](https://aclanthology.org/2022.emnlp-main.156/)的作者。

## 安装

### 安装为终端命令

推荐读者直接用 [uv](https://docs.astral.sh/uv/) 或 `pipx` 将 AnnaAgent 安装成终端命令：

```bash
# 安装 GitHub 最新版本为独立命令行工具。
uv tool install git+https://github.com/sci-m-wang/AnnaAgent.git

# 如果使用 pipx：
pipx install git+https://github.com/sci-m-wang/AnnaAgent.git
```

安装完成后，任意终端中都可以使用短命令 `anna`：

```bash
anna --version
anna init anna-workspace
anna doctor --workspace anna-workspace
```

较长的命令名 `anna-agent` 仍然保留为兼容别名。

如果你希望 AnnaAgent 自动用 vLLM 启动本地 SFT 模型，建议在 Linux/GPU 机器上创建 workspace 级部署环境。这样轻量的 `anna` CLI 安装和较重的 vLLM 依赖相互隔离：

```bash
anna init anna-workspace --deploy-env

# 或者对已有 workspace 后续补建。
anna models env setup --workspace anna-workspace
anna models env status --workspace anna-workspace
```

部署环境默认位于 `anna-workspace/.anna-deploy-venv`，默认使用 Python 3.12。`anna models deploy` 会自动优先使用 `anna-workspace/.anna-deploy-venv/bin/vllm`。如果集群中已经有其他 conda/module 环境提供 vLLM，也可以继续使用普通 AnnaAgent 安装，并在部署时显式指定 vLLM 可执行文件：

```bash
anna models deploy --target complaint --workspace anna-workspace \
  --vllm-command /path/to/vllm
```

### 从源码开发

如果你要修改代码，可以在项目本地 `.venv` 中安装依赖：

```bash
git clone https://github.com/sci-m-wang/AnnaAgent.git
cd AnnaAgent
uv sync
uv run anna --help
```

也可以把本地源码安装成终端命令：

```bash
uv tool install --editable .
anna --help
```

## 快速开始

创建一个独立工作区并检查环境：

```bash
anna init anna-workspace
anna doctor --workspace anna-workspace
```

工作区会包含 `settings.yaml`、`.env`、样例案例、提示词状态、运行结果、日志、缓存和资产 manifest。

启动一个样例交互：

```bash
anna demo --workspace anna-workspace
```

运行 `anna` 不带子命令时，会默认读取工作区中的 `interactive.yaml` 并启动交互式对话。

## CLI 使用流程

AnnaAgent 的 CLI 围绕“论文读者从复现实验到实际应用”的完整旅程设计。

### 1. 初始化工作区

```bash
anna init anna-workspace

# GPU 机器可选：同时创建 anna-workspace/.anna-deploy-venv 供 vLLM 使用。
anna init anna-workspace --deploy-env
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
anna config wizard --workspace anna-workspace
anna config secrets --workspace anna-workspace
anna config set model_service.base_url https://example.com/v1 \
  --workspace anna-workspace
anna config show --workspace anna-workspace
anna config validate --workspace anna-workspace
```

`config wizard` 和 `config secrets` 会用隐藏密码输入模式读取 API key，并写入 `.env`。初始化时生成的 `.env` 和 `.env.example` 已包含 base model、SFT model、embedding 等 key 的注释占位符；如果你想手动编辑，直接在对应占位符下面取消注释并填写即可。API key 等敏感信息不要提交到 Git。

### 3. 下载论文资产

资产下载由 `assets/anna-assets.json` 管理。默认 `paper` preset 指向已发布的 HuggingFace SFT 模型和合成数据：

```bash
anna assets list --workspace anna-workspace
anna assets pull paper --workspace anna-workspace
```

下载资产时请始终传入 `--workspace` 或 `--manifest`。如果两个都不传，`anna assets pull` 会把当前目录当成工作区，可能下载到 `./assets/...`，而不是你的 AnnaAgent 工作区。你可以只下载某一个资源，也可以显式覆盖目标目录：

```bash
# 从 anna-workspace/assets/anna-assets.json 下载单个资源。
anna assets pull complaint-sft --workspace anna-workspace

# 直接指定资产 JSON；其中的绝对 target 路径会被原样使用。
anna assets pull complaint-sft --manifest anna-workspace/assets/anna-assets.json

# 对单个资源显式指定下载目录。
anna assets pull complaint-sft --workspace anna-workspace \
  --target /path/to/models/complaint-sft
```

默认资产包括：

- 情绪推断 SFT 模型：`sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct`
- 主诉链生成 SFT 模型：`sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct`
- 合成标准数据：`sci-m-wang/Anna-CPsyCounD`

你也可以编辑 `assets/anna-assets.json`，加入自己的 HuggingFace 仓库或直接下载 URL。

### 3.1 显式选择 base 模型或 SFT 模型

情绪推断器和主诉链生成器不应该靠读者手动部署后再填写 key。AnnaAgent 现在提供两条路径：

- **自行指定 endpoint**：如果你已经部署了 OpenAI-compatible SFT 服务，用 `anna models configure` 写入配置。
- **本地 vLLM 自动部署**：如果你有 GPU 和 vLLM，用 `anna models deploy --backend vllm` 自动启动服务并写回配置。

如果只是想先跑通流程，可以明确使用 base model：

```bash
anna models use-base --target all --workspace anna-workspace
```

如果要使用 SFT 模型，可以先下载论文资产，然后自动部署：

```bash
anna assets pull paper --workspace anna-workspace
anna models env setup --workspace anna-workspace  # 如果 init 时已用 --deploy-env，可跳过
anna models env status --workspace anna-workspace
anna models deploy --target complaint --backend vllm --workspace anna-workspace
anna models deploy --target emotion --backend vllm --workspace anna-workspace
anna models status --workspace anna-workspace
```

也可以接入你自己部署好的 SFT endpoint：

```bash
anna models configure --target complaint \
  --base-url http://127.0.0.1:8001/v1 \
  --model-name complaint \
  --workspace anna-workspace

anna models configure --target emotion \
  --base-url http://127.0.0.1:8000/v1 \
  --model-name emotion \
  --workspace anna-workspace
```

`models deploy` 会启动后台 vLLM OpenAI-compatible 服务，把服务地址、模型名和 `use_sft_model` 写回 `settings.yaml`，把 API key 写入 `.env`，并在 `logs/services/` 与 `runs/services/` 下记录日志和 PID。可以加 `--dry-run` 只查看将要执行的 vLLM 命令。

如果没有传 `--model-path`，`models deploy` 会从 `assets/anna-assets.json` 中读取对应 SFT 资源的 target 路径，包括你在 JSON 中写的绝对路径。请确保 deploy 时使用和 pull 时相同的 `--workspace` 或 `--manifest`。

如果 `models deploy` 提示找不到 vLLM，请先运行 `anna models env setup --workspace anna-workspace` 创建 workspace 级部署环境，或用 `--vllm-command` 指向集群/conda 环境中已有的 vLLM 可执行文件。

### 4. 数据准备与校验

运行实验前建议先校验案例格式：

```bash
anna data validate anna-workspace/cases/family_stress_case.json
anna data inspect anna-workspace/cases/family_stress_case.json
anna data sample --out anna-workspace/cases/sample.json
```

案例文件主要包含：

- `portrait`：来访者画像、风险分数和症状
- `report`：结构化咨询案例报告
- `conversation` 或 `previous_conversations`：前一疗程对话历史

### 5. 连通性测试

正式运行昂贵实验前，建议单独测试模型、embedding 和记忆库：

```bash
anna test embedding --workspace anna-workspace
anna test memory --workspace anna-workspace
anna test model --workspace anna-workspace
anna test all --workspace anna-workspace
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
anna memory index anna-workspace/cases/family_stress_case.json \
  --workspace anna-workspace
```

检索长期记忆：

```bash
anna memory search "胸闷和家庭压力" \
  --workspace anna-workspace \
  --seeker-id 42289a5f-bbdc-43f9-826a-9569bbbd5feb
```

查看或重置记忆库：

```bash
anna memory stats --workspace anna-workspace
anna memory inspect --workspace anna-workspace
anna memory reset --workspace anna-workspace --yes
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
anna initialize prompt-only anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.prompt.json

anna initialize full anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.full.json \
  --workspace anna-workspace

anna initialize freeze anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.frozen.json \
  --workspace anna-workspace

anna initialize from-prompt anna-workspace/prompts/family.prompt.json
```

### 9. 交互式对话

可以从案例文件启动，也可以从固定 prompt state 启动：

```bash
anna chat --workspace anna-workspace \
  --case anna-workspace/cases/family_stress_case.json \
  --save anna-workspace/runs/manual-chat.jsonl

anna chat --workspace anna-workspace \
  --state anna-workspace/prompts/family.prompt.json
```

### 10. 批量实验

默认批量运行只生成初始化状态，不调用模型；添加 `--live` 后会执行脚本化对话。

```bash
anna run batch --workspace anna-workspace \
  --case 'cases/*.json' \
  --out anna-workspace/runs/batch

anna run batch --workspace anna-workspace \
  --case 'cases/*.json' \
  --script scripts/counselor_messages.json \
  --live \
  --out anna-workspace/runs/live-batch
```

### 11. 启动接口服务

可以启动一个轻量 JSON API 服务，供外部实验驱动或应用调用：

```bash
anna serve --workspace anna-workspace --host 127.0.0.1 --port 8000
```

当前服务包含：

- `GET /health`
- `GET /v1/sessions`
- `POST /v1/sessions`
- `POST /v1/chat`
- `POST /v1/memory/search`

### 12. 日志、缓存与清理

```bash
anna logs tail anna-workspace/logs/anna-agent.log
anna cache list --workspace anna-workspace
anna cache clean --workspace anna-workspace --yes
anna reset workspace --workspace anna-workspace --yes
anna doctor --workspace anna-workspace
```

## 选择基础模型或 SFT 模型

情绪推断器和主诉链生成器可以使用 `model_service` 中的基础模型，也可以使用自行部署的 SFT endpoint，或由 AnnaAgent 通过 vLLM 自动部署的本地 SFT 服务。推荐优先使用 CLI 命令，而不是手动改 YAML：

```bash
anna models use-base --target all --workspace anna-workspace
anna models use-sft --target all --workspace anna-workspace
anna models configure --target emotion \
  --base-url http://127.0.0.1:8000/v1 \
  --model-name emotion \
  --workspace anna-workspace
anna models env setup --workspace anna-workspace
anna models deploy --target emotion --backend vllm --workspace anna-workspace
```

如果需要手动配置，也可以在 `settings.yaml` 中设置 `use_sft_model`。`false` 表示回退到基础模型，`true` 表示调用对应 SFT endpoint：

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
  uv run anna
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
