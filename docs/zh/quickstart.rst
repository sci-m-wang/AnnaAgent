快速开始
========

本页从一台干净机器开始，带你完成安装、创建 workspace、配置模型并运行样例。为了降低门槛，默认使用 base model 路径。

准备条件
--------

* Python 3.10 或更新版本。
* ``uv``、``pipx`` 或 ``pip`` 之一。
* 一个 OpenAI-compatible chat model endpoint 和 API key。
* 如果要使用长期记忆，还需要一个 OpenAI-compatible embedding endpoint。

安装 CLI
--------

推荐从 PyPI 安装成独立终端命令：

.. code-block:: bash

   uv tool install anna-agent
   anna --version

如果使用 ``pipx``：

.. code-block:: bash

   pipx install anna-agent
   anna --version

如果你要从源码开发：

.. code-block:: bash

   git clone https://github.com/sci-m-wang/AnnaAgent.git
   cd AnnaAgent
   uv sync
   uv run anna --help

创建 Workspace
--------------

AnnaAgent 会把用户配置、密钥、样例案例、运行结果、日志和记忆库放在 workspace 中：

.. code-block:: bash

   anna init anna-workspace
   anna doctor --workspace anna-workspace

生成结构如下：

.. code-block:: text

   anna-workspace/
     settings.yaml
     .env
     .env.example
     assets/
     cases/
     prompts/
     runs/
     outputs/
     logs/
     cache/

配置基础模型
------------

使用交互式向导：

.. code-block:: bash

   anna config wizard --workspace anna-workspace
   anna config secrets --workspace anna-workspace
   anna config validate --workspace anna-workspace

也可以用非交互命令设置非密钥字段：

.. code-block:: bash

   anna config set model_service.base_url https://example.com/v1 --workspace anna-workspace
   anna config set model_service.model_name your-chat-model --workspace anna-workspace
   anna config show --workspace anna-workspace

选择轻量模式
------------

第一次运行建议让所有模块都使用 base model：

.. code-block:: bash

   anna models use-base --target all --workspace anna-workspace
   anna models status --workspace anna-workspace

运行样例对话
------------

启动内置样例：

.. code-block:: bash

   anna demo --workspace anna-workspace

也可以直接运行 workspace 中默认的 ``interactive.yaml``：

.. code-block:: bash

   anna --workspace anna-workspace

输入 ``exit``、``quit`` 或 ``q`` 退出对话。

生成 Prompt-Only 状态
---------------------

Prompt-only 模式会把案例冻结成一个 system prompt，适合快速实验和 API session：

.. code-block:: bash

   anna initialize prompt-only anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/prompts/family_stress.prompt-only.json

   anna initialize from-prompt anna-workspace/prompts/family_stress.prompt-only.json

批量运行
--------

.. code-block:: bash

   anna run batch \
     --case anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/runs/quickstart \
     --mode prompt-only \
     --workspace anna-workspace

如果要真的调用模型生成对话，再额外提供 ``--live`` 和 ``--script``。
