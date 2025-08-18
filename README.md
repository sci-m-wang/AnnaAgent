# AnnaAgent

The code for the paper `AnnaAgent: Dynamic Evolution Agent System with Multi-Session Memory for Realistic Seeker Simulation`.

## CLAIM

It is important to note that since this work involves data from counselling records of **real patients** with psychological disorders, the publicly available code can only be used to demonstrate part of the methodology. Please contact the authors of [this paper](https://aclanthology.org/2022.emnlp-main.156/) if needed.

## Installation

Install the project dependencies using pip:

```bash
pip install -e .
```

## How to Run the Example
First, you need to deploy the servers with these commands:

```bash
# need vllm, the version we used is 0.6.4.
bash complaint.sh
bash counselor.sh
bash emotion.sh
```

The trained model will be updated here at the end of the submission progress. You can also use an untrained LLM as an alternative, it might be less effective.

There is an inner example provided through the `anna-agent` CLI. Install the dependencies and
initialize the project before starting the demo:

```bash
python -m anna_agent.initialize
anna-agent
```

After initialization you can chat with the virtual seeker.

## CLI Usage

AnnaAgent provides a small Typer-based command line interface with two entry
points. After initializing the project you can either run the built-in demo or
start a conversation using your own `interactive.yaml`.

### Demo

Launch the demo seeker defined in the source code:

```bash
anna-agent demo
```

Both `demo` and the main command accept `--workspace` (also available as
`--root`) to specify the project directory. Each workspace directory should
contain both a `settings.yaml` and an `interactive.yaml` file.

### Interactive mode

Running `anna-agent` without a subcommand uses the `interactive.yaml` in the
project directory and starts chatting with the virtual seeker:

```bash
anna-agent
```

## Project Initialization

The repository offers a small helper to generate default configuration files.
Run the initialization script once before starting the example. It creates
a `settings.yaml`, an `interactive.yaml` and `.env` in the target directory:

```bash
python -m anna_agent.initialize
```

The generated `settings.yaml` contains the model service settings and per-module
server configuration including API keys, base URLs and model names for the
complaint, counselor and emotion modules. `interactive.yaml` holds a sample
portrait, report and conversation history used by the main CLI. Environment
variables are written to `.env` with the `ANNA_ENGINE_` prefix for easy
override.

### `interactive.yaml` Overview

`interactive.yaml` defines the virtual seeker's configuration. The main fields are:

- **portrait** – basic profile and psychological risk scores (e.g. `drisk`, `srisk`).
- **report** – case description including categories and applied techniques.
- **previous_conversations** – optional conversation history from earlier sessions.

A ready-to-use example can be found at [docs/interactive_demo.yaml](docs/interactive_demo.yaml). It follows the psychological scale format used by the project and can be copied as your starting configuration.

The `anna_agent` package loads its configuration from the workspace directory at
runtime using `settings.yaml`. By default the current working directory is used,
but you can override the location by setting the `ANNA_AGENT_WORKSPACE`
environment variable.  When using the library programmatically you can also
call `anna_agent.backbone.configure(<workspace>)` to load the desired
configuration on demand.

## Work Progress

To make it easier for readers to learn how to use it, we have added the flowchart below:

![](https://github.com/sci-m-wang/AnnaAgent/blob/main/figure/whiteboard_exported_image_en.png)

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
