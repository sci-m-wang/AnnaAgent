配置与 Workspace
================

AnnaAgent 将项目代码和运行状态分离。仓库中保存 package；每个 workspace 保存配置、密钥、生成状态、日志和本地记忆库。

Workspace 文件
--------------

``settings.yaml``
  非密钥配置，例如 base URL、模型名、SFT endpoint、记忆设置和资产信息。

``.env``
  本地密钥，例如 API key。不要提交到 Git。

``.env.example``
  注释形式的密钥占位符，方便手动配置。

``assets/anna-assets.json``
  HuggingFace 仓库、直接下载资源和本地 SFT 目标路径的 manifest。

``cases/``
  CLI 和 batch run 使用的 JSON/YAML 案例。

``prompts/``
  frozen prompt state 和 full initialization state。

``runs/`` 与 ``logs/``
  实验输出、vLLM 服务 PID 和日志。

查看和修改配置
--------------

.. code-block:: bash

   anna config show --workspace anna-workspace
   anna config show --no-redact --workspace anna-workspace
   anna config set model_service.base_url https://example.com/v1 --workspace anna-workspace
   anna config validate --workspace anna-workspace

只有在可信终端中才使用 ``--no-redact``。API key 建议通过 ``anna config secrets`` 输入，或者写入 workspace 的 ``.env``。

模型模式
--------

AnnaAgent 常用三种模型模式。

Base model 模式
  最简单。所有模块调用同一个基础 chat model。建议先用它跑通流程。

已部署 SFT endpoint 模式
  如果你已经部署了 complaint 或 emotion SFT OpenAI-compatible 服务，用 ``models configure`` 写入地址。

本地 vLLM 部署模式
  在 Linux/GPU 机器上，让 AnnaAgent 自动启动 SFT 服务并写回 workspace 配置。

常用命令：

.. code-block:: bash

   anna models use-base --target all --workspace anna-workspace
   anna models use-sft --target all --workspace anna-workspace
   anna models status --workspace anna-workspace

   anna models configure --target complaint \
     --base-url http://127.0.0.1:8001/v1 \
     --model-name complaint \
     --workspace anna-workspace

安全建议
--------

* 不提交 ``.env``。
* API key 使用环境变量或 ``anna config secrets``。
* 公开 issue 和日志中只使用脱敏输出。
* 不要把真实心理咨询记录粘贴到公开 issue 或公开模型 prompt 中。
