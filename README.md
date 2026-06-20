# AnnaAgent

[中文说明](README.zh-CN.md) | English

The code for the paper `AnnaAgent: Dynamic Evolution Agent System with Multi-Session Memory for Realistic Seeker Simulation`.

> **Important repository update:** We have removed the previous web application
> code and refactored this repository into a cleaner AnnaAgent core toolkit so
> that the method is easier to understand, install, and use for experiments or
> downstream applications. If you need the web application, please use the
> deployed site at [anna.kinamind.org](https://anna.kinamind.org/) or the
> AnnApod repository at [github.com/kinamind/annapod](https://github.com/kinamind/annapod).

## CLAIM

It is important to note that since this work involves data from counselling records of **real patients** with psychological disorders, the publicly available code can only be used to demonstrate part of the methodology. Please contact the authors of [this paper](https://aclanthology.org/2022.emnlp-main.156/) if needed.

## Installation

### Install as a terminal command

For most readers, install AnnaAgent from PyPI as a terminal command with
[uv](https://docs.astral.sh/uv/) or `pipx`:

```bash
# Install the latest PyPI release as a standalone tool.
uv tool install anna-agent

# Or, if you use pipx:
pipx install anna-agent

# Or, if you prefer pip in an existing environment:
pip install anna-agent
```

After installation, the short command `anna` is available in any terminal:

```bash
anna --version
anna create anna-workspace
anna doctor --workspace anna-workspace
```

The longer command name `anna-agent` is kept as a compatibility alias.

If you want AnnaAgent to automatically start local SFT models with vLLM, create
a workspace deployment environment on the Linux/GPU machine. This keeps the
lightweight `anna` CLI install separate from heavy vLLM dependencies:

```bash
anna create anna-workspace --deploy-env

# Or add it later to an existing workspace.
anna models env setup --workspace anna-workspace
anna models env status --workspace anna-workspace
```

The deploy environment is created under `anna-workspace/.anna-deploy-venv` with
Python 3.12 by default. `anna models deploy` automatically uses
`anna-workspace/.anna-deploy-venv/bin/vllm` when it exists. If your cluster
already provides vLLM in another environment, keep the normal AnnaAgent install
and pass that executable explicitly when deploying:

```bash
anna models deploy --target complaint --workspace anna-workspace \
  --vllm-command /path/to/vllm
```

### Develop from source

If you are modifying the code, install the project dependencies into a
project-local `.venv` using `uv`:

```bash
git clone https://github.com/sci-m-wang/AnnaAgent.git
cd AnnaAgent
uv sync
uv run anna --help
```

The full bilingual documentation is available from the GitHub Pages site:
`https://sci-m-wang.github.io/AnnaAgent/`.

You can also expose the local checkout as the terminal command:

```bash
uv tool install --editable .
anna --help
```

## How to Run the Example
First, create a workspace, choose whether to use the SFT modules, and let the CLI
write the resulting configuration:

```bash
anna create anna-workspace

# Optional on GPU machines: create anna-workspace/.anna-deploy-venv for vLLM.
anna create anna-workspace --deploy-env

# Fast path: use the base chat model for complaint-chain and emotion modules.
anna models use-base --target all --workspace anna-workspace

# SFT path: deploy local vLLM services from downloaded HuggingFace assets.
anna assets download paper --workspace anna-workspace
anna models env setup --workspace anna-workspace  # optional if create used --deploy-env
anna models deploy --target complaint --backend vllm --workspace anna-workspace \
  --gpu 0 --gpu-memory-utilization 0.85 --wait-timeout 900
anna models deploy --target emotion --backend vllm --workspace anna-workspace \
  --gpu 1 --gpu-memory-utilization 0.85 --wait-timeout 900
```

You can also connect self-hosted OpenAI-compatible SFT endpoints instead of
letting AnnaAgent start vLLM:

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

Using the base model is easier to start with. The SFT modules usually produce
more faithful emotion inference and chief-complaint chains when GPU resources
are available.

There is an inner example provided through the `anna` CLI. Install the dependencies and
initialize the project before starting the demo:

```bash
uv run python -m anna_agent.initialize
uv run anna
```

After initialization you can chat with the virtual seeker.

## CLI Usage

AnnaAgent provides a Typer-based CLI organized around the reader journey from
paper reproduction to application use. Start by creating an isolated workspace:

```bash
anna create anna-workspace
anna doctor --workspace anna-workspace
```

The workspace contains `settings.yaml`, `.env`, sample cases, prompts, run
outputs, logs, cache files and an asset manifest. Configure model endpoints with
the wizard or non-interactive setters:

```bash
anna config wizard --workspace anna-workspace
anna config secrets --workspace anna-workspace
anna config set model_service.base_url https://example.com/v1 \
  --workspace anna-workspace
anna config show --workspace anna-workspace
anna config validate --workspace anna-workspace
```

`config wizard` and `config secrets` use hidden password-style prompts for API
keys and write them to `.env`. The generated `.env` and `.env.example` files
include commented placeholders showing exactly where to put backbone, SFT and
embedding credentials if you prefer manual editing.

Assets are manifest-driven. The default `paper` preset points to the released
HuggingFace SFT models and synthetic data, and you can override or extend it in
`assets/anna-assets.json` with your own repositories or direct URLs:

```bash
anna assets list --workspace anna-workspace
anna assets download paper --workspace anna-workspace
```

Always pass `--workspace` or `--manifest` when downloading assets. Without either,
`anna assets download` uses the current directory as the workspace and may download
to `./assets/...` instead of your intended AnnaAgent workspace. You can download one
specific resource or override the target directory explicitly:

```bash
# Download one asset from anna-workspace/assets/anna-assets.json.
anna assets download complaint-sft --workspace anna-workspace

# Use an explicit manifest JSON, including absolute target paths in that file.
anna assets download complaint-sft --manifest anna-workspace/assets/anna-assets.json

# Override the target directory for exactly one selected asset.
anna assets download complaint-sft --workspace anna-workspace \
  --target /path/to/models/complaint-sft
```

Choose the model mode explicitly before experiments. Use the base model for the
lowest setup cost, configure existing SFT endpoints if you already deployed them,
or let AnnaAgent start local vLLM services:

```bash
anna models use-base --target all --workspace anna-workspace
anna models use-sft --target all --workspace anna-workspace
anna models status --workspace anna-workspace

anna models configure --target complaint \
  --base-url http://127.0.0.1:8001/v1 \
  --model-name complaint \
  --workspace anna-workspace

anna models env setup --workspace anna-workspace
anna models env status --workspace anna-workspace
anna models deploy --target complaint --backend vllm --workspace anna-workspace \
  --gpu 0 --gpu-memory-utilization 0.85 --wait-timeout 900
anna models deploy --target emotion --backend vllm --workspace anna-workspace \
  --gpu 1 --gpu-memory-utilization 0.85 --wait-timeout 900
```

`models deploy` starts a vLLM OpenAI-compatible server in the background, writes
the service URL/model name/use-SFT flag back to `settings.yaml`, writes API keys
to `.env`, and records logs/PIDs under `logs/services/` and `runs/services/`.
Before starting vLLM, it runs a GPU preflight check with `nvidia-smi`, prints the
selected GPU, free memory, and vLLM memory cap, and blocks obvious failures such
as a missing GPU ID or insufficient free memory. Before writing configuration,
it waits for the service to answer `/v1/models`; use `--wait-timeout 900` for
slow model loads. If startup fails or times out, the CLI prints the service log
tail and does not write a bad endpoint. Use `--dry-run` to print the vLLM command
without starting anything.
It also checks for a CUDA toolkit (`nvcc`) without assuming a fixed CUDA module
name or version. If a valid toolkit is found through `--cuda-home`, `CUDA_HOME`,
`PATH`, or common CUDA roots, AnnaAgent injects `CUDA_HOME`, `PATH`, and
`LD_LIBRARY_PATH` only into the vLLM child process. If no toolkit is visible on a
module-based cluster, AnnaAgent inspects available CUDA modules and auto-loads
the default CUDA module for the vLLM process; if no default is marked, it uses
the highest available version. If no toolkit or CUDA module can be found, the
CLI warns and continues because some vLLM environments do not require `nvcc`;
FlashInfer JIT environments usually do. No manual `module load` is required.
The deploy preflight also checks for the `ninja` build tool required by
FlashInfer JIT. If the workspace deploy environment is missing it,
`models deploy` installs it into that workspace before starting vLLM. Use
`--cuda-home` only when the cluster stores CUDA in a custom location:

```bash
anna models deploy --target complaint --backend vllm --workspace anna-workspace \
  --gpu 0 --gpu-memory-utilization 0.85 --wait-timeout 900

anna models deploy --target complaint --backend vllm --workspace anna-workspace \
  --gpu 0 --cuda-home /path/to/cuda --gpu-memory-utilization 0.85
```
When `--model-path` is omitted, deploy reads the corresponding SFT asset target
from `assets/anna-assets.json`, including absolute paths. Pass the same
`--workspace` or `--manifest` that you used during `assets download`.

If `models deploy` reports that vLLM is unavailable, run
`anna models env setup --workspace anna-workspace` to create the workspace deploy
environment, or pass `--vllm-command` to a vLLM executable provided by your
cluster/conda environment.

Validate and prepare case data before running experiments:

```bash
anna data validate anna-workspace/cases/family_stress_case.json
anna data inspect anna-workspace/cases/family_stress_case.json
anna data sample --out anna-workspace/cases/sample.json
```

Run connectivity checks separately from expensive experiments:

```bash
anna test embedding --workspace anna-workspace
anna test memory --workspace anna-workspace
anna test model --workspace anna-workspace
```

Initialization can be run as a full AnnaAgent initialization, or as a prompt-only
state for cheap dry-runs and reproducible prompt freezing:

```bash
anna init prompt-only anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.prompt.json
anna init full anna-workspace/cases/family_stress_case.json \
  --out anna-workspace/prompts/family.full.json --workspace anna-workspace
anna init from-prompt anna-workspace/prompts/family.prompt.json
```

Chat interactively from either a case file or a frozen prompt state:

```bash
anna chat --workspace anna-workspace \
  --case anna-workspace/cases/family_stress_case.json \
  --save anna-workspace/runs/manual-chat.jsonl
anna chat --workspace anna-workspace \
  --state anna-workspace/prompts/family.prompt.json
```

Batch experiments support dry-run initialization by default and live scripted
conversation when `--live` is supplied:

```bash
anna run batch --workspace anna-workspace \
  --case 'cases/*.json' --out anna-workspace/runs/batch
anna run batch --workspace anna-workspace \
  --case 'cases/*.json' --script scripts/counselor_messages.json \
  --live --out anna-workspace/runs/live-batch
```

Start the lightweight JSON API service for external experiment drivers:

```bash
anna serve --workspace anna-workspace --host 127.0.0.1 --port 8000
```

Diagnostics and cleanup commands are available for local workflows:

```bash
anna logs tail anna-workspace/logs/anna-agent.log
anna cache list --workspace anna-workspace
anna cache clean --workspace anna-workspace --yes
anna reset workspace --workspace anna-workspace --yes
```

Running `anna` without a subcommand still starts interactive chat from the
workspace `interactive.yaml`; `anna demo` creates a sample case if needed
and starts an example chat.

## Project Initialization

The repository offers a small helper to generate default configuration files.
Run the initialization script once before starting the example. It creates
a `settings.yaml`, an `interactive.yaml` and `.env` in the target directory:

```bash
uv run python -m anna_agent.initialize
```

The generated `settings.yaml` contains the model service settings and per-module
server configuration including API keys, base URLs and model names for the
complaint, counselor and emotion modules. `interactive.yaml` holds a sample
portrait, report and conversation history used by the main CLI. Environment
variables are written to `.env` with the `ANNA_ENGINE_` prefix for easy
override.

### Complete Run with a Sample Case

The repository includes a family-stress sample case at
`docs/family_stress_case.json`:

- `id`: `42289a5f-bbdc-43f9-826a-9569bbbd5feb`
- `conversation`: previous-session conversation history used as long-term memory
- `report`: structured counseling case report
- `portrait`: seeker profile and symptoms

Run a complete one-turn example with the sample case:

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

The two `ANNA_ENGINE_*_USE_SFT_MODEL=false` flags make the emotional inferencer
and chief complaint chain generator use the base model configured in
`model_service`. This is useful when the SFT checkpoints are unavailable.

### Long-Term Memory with LanceDB

AnnaAgent stores long-term memory in a local LanceDB database. Previous-session
conversations and reports are chunked into `conversation_turn`,
`conversation_window`, `session_summary`, `report_section`, and `report_summary`
records. Session metadata is stored alongside the vector table, so future runs
can accumulate multiple sessions for the same seeker.

By default, memory data is written to `.anna_memory/`, which is ignored by Git.
The embedding layer first tries the configured OpenAI-compatible embedding model
and automatically falls back to a deterministic local hash embedding when the
embedding service is unavailable.

Embedding credentials can use the AnnaAgent names or common OpenAI-style aliases
in `.env`:

```bash
ANNA_ENGINE_EMBEDDING_API_KEY=...
ANNA_ENGINE_EMBEDDING_BASE_URL=https://your-embedding-endpoint/v1
ANNA_ENGINE_EMBEDDING_MODEL_NAME=your-embedding-model

# Also supported:
OPENAI_EMBEDDING_API_KEY=...
OPENAI_EMBEDDING_BASE_URL=https://your-embedding-endpoint/v1
OPENAI_EMBEDDING_MODEL=your-embedding-model
```

Index the sample case into long-term memory:

```bash
anna memory index docs/family_stress_case.json
```

Search a seeker's long-term memory:

```bash
anna memory search "胸闷和家庭压力" \
  --seeker-id 42289a5f-bbdc-43f9-826a-9569bbbd5feb
```

During normal interactive runs, AnnaAgent can auto-index the current
`interactive.json` / `interactive.yaml` previous-session data and use retrieved
memory when a counselor utterance refers to prior sessions or historical context.

### Choosing Base Models or SFT Models

The emotional inferencer and chief complaint chain generator can either use the
base model configured in `model_service`, self-hosted SFT endpoints, or local
vLLM services launched by AnnaAgent. Prefer the explicit CLI commands over
manual YAML edits:

```bash
anna models use-base --target all --workspace anna-workspace
anna models use-sft --target all --workspace anna-workspace
anna models configure --target emotion \
  --base-url http://127.0.0.1:8000/v1 \
  --model-name emotion \
  --workspace anna-workspace
anna models env setup --workspace anna-workspace
anna models deploy --target emotion --backend vllm --workspace anna-workspace \
  --gpu 1 --gpu-memory-utilization 0.85 --wait-timeout 900
```

Manual configuration is still supported. Set `use_sft_model` to `false` to use
the base model, or `true` to call the configured SFT endpoint.

```yaml
model_service:
  model_name: anna-backbone
  api_key: anna-backbone
  base_url: http://localhost:8002/v1
servers:
  complaint:
    use_sft_model: false
  emotion:
    use_sft_model: false
```

### `interactive.yaml` Overview

`interactive.yaml` defines the virtual seeker's configuration. The main fields are:

- **portrait** – basic profile and psychological risk scores (e.g. `drisk`, `srisk`).
- **report** – case description including categories and applied techniques.
- **previous_conversations** – optional conversation history from earlier sessions.

A ready-to-use example can be found at [docs/interactive_demo.yaml](docs/interactive_demo.yaml). It follows the psychological scale format used by the project and can be copied as your starting configuration.
Another complete sample is [docs/family_stress_case.json](docs/family_stress_case.json), which uses `conversation` as the previous-session conversation field and `marital_status` as a supported alias for `martial_status`.

The `anna_agent` package loads its configuration from the workspace directory at
runtime using `settings.yaml`. By default the current working directory is used,
but you can override the location by setting the `ANNA_AGENT_WORKSPACE`
environment variable.  When using the library programmatically you can also
call `anna_agent.backbone.configure(<workspace>)` to load the desired
configuration on demand.

## Work Progress

To make it easier for readers to learn how to use it, we have added the flowchart below:

![](https://github.com/sci-m-wang/AnnaAgent/blob/main/src/anna_agent/figure/whiteboard_exported_image_en.png)

With two groups of agents (for **Dynamic Evolution** & **Multi-session Memory**, respectively), AnnaAgent simulates seekers via two main stages, i.e., the **initialization stage** to set the seeker's configuration (including profile, situation, symptoms, etc) and the **conversation stage** to interact with the counselor. The agent group for dynamic evolution contains an emotion modulator, a chief complaint chain generator and a complaint switcher. There are three agents in the agent group for multi-session memory: a situation analyzer, a status analyzer, and a memory retriever.

In addition, there are supplementary modules for speaking style analysis, scale summarization and event selection.

At the initialization stage, the seeker's **basic profile** and historical session conversations and reports from **long-term memory** are first read. The seeker's style is analyzed based on the previous session's conversations by the *speaking style analysis module* next. The *scale summarization module* summarizes **historical scales** based on the seeker's profile and reports. Then, the *event selection module* matches a suitable event based on the seeker's profile and the *situation analyzer* generates a situation that the seeker encounters based on the event. Meanwhile, the virtual seeker is required to complete the scales for the **current session** based on the current configurations and the *status analyzer* analyzes the change in the seeker's status based on the two groups of scales. Situations and statuses together make up **short-term memory**. In addition, the **chief complaint chain generator** generates a chief complaint chain based on the seeker's profile and long-term memory during the initialization stage.

At the **conversation stage**, AnnaAgent has a conversation with a counselor. For each utterance by the counselor, the *memory retriever* determines whether long-term memory needs to be **retrieved**. If it is needed, relevant information is retrieved from conversations and reports from **previous sessions**. In addition, the *emotion modulator* reasons the **seeker's next emotion** and performs emotion perturbation on a probability basis according to the real-time memory, i.e., the context of the conversation. After the seeker completes an utterance, the *complaint switcher* decides whether or not to awaken the seeker's **next chief complaint stage**.

## Models
The training data for both the emotional inferencer and the chief complaint chain generator are derived from real data. We did not open source the labeled raw data due to ethical risk concerns. To facilitate further research and application, we set the models to be conditionally public.

| Model | Link | Backbone |
| --- | --- | --- |
| The Emotional Inferencer | [link](https://huggingface.co/sci-m-wang/Emotion_inferencer-Qwen2.5-7B-Instruct) | Qwen2.5-7B-Instruct |
| Chief Complaint Chain Generator | [link](https://huggingface.co/sci-m-wang/Chief_chain_generator-Qwen2.5-7B-Instruct) | Qwen2.5-7B-Instruct |

In addition, we will continue to train and release emotion inferencers and chief complaint chain generators based on more models with different architectures.

## Synthetic Data
We used the [CPsyCounD](https://github.com/CAS-SIAT-XinHai/CPsyCoun) dataset as a seed to synthesize a seeker bank that meets the requirements of the AnnaAgent format using GPT-4o-mini. It can be found at this [link](https://huggingface.co/datasets/sci-m-wang/Anna-CPsyCounD). We will continue to transform more data and will create more realistic seeker characters based on AnnaAgent for use in related research.
## Developer Guide

For contribution guidelines refer to:
- [开发者指南 (Chinese)](src/docs/contributing/code.md)
- [Developer Guide (English)](src/docs/contributing/code_en.md)


## Citation
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
