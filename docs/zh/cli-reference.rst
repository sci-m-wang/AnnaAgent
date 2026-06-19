CLI 命令参考
============

短命令是 ``anna``，兼容别名是 ``anna-agent``。

全局命令
--------

.. code-block:: bash

   anna --version
   anna --help
   anna doctor --workspace anna-workspace
   anna init anna-workspace
   anna chat --workspace anna-workspace
   anna demo --workspace anna-workspace

``doctor`` 会检查安装、workspace 配置和常见运行条件。正式实验前建议先运行。

资产
----

.. code-block:: bash

   anna assets list --workspace anna-workspace
   anna assets pull paper --workspace anna-workspace
   anna assets pull complaint-sft --workspace anna-workspace
   anna assets pull complaint-sft --manifest anna-workspace/assets/anna-assets.json

下载资产时始终传 ``--workspace`` 或 ``--manifest``，避免下载到错误目录。

模型
----

.. code-block:: bash

   anna models use-base --target all --workspace anna-workspace
   anna models use-sft --target complaint --workspace anna-workspace
   anna models status --workspace anna-workspace
   anna models configure --target emotion \
     --base-url http://127.0.0.1:8000/v1 \
     --model-name emotion \
     --workspace anna-workspace

本地 vLLM 部署见 :doc:`deployment`。

数据
----

.. code-block:: bash

   anna data validate anna-workspace/cases/family_stress_case.json
   anna data inspect anna-workspace/cases/family_stress_case.json
   anna data sample --out anna-workspace/cases/sample.json
   anna data convert input.yaml --out anna-workspace/cases/input.json

记忆
----

.. code-block:: bash

   anna memory index anna-workspace/cases/family_stress_case.json --workspace anna-workspace
   anna memory search "家庭压力和睡眠问题" --workspace anna-workspace
   anna memory stats --workspace anna-workspace
   anna memory inspect --workspace anna-workspace
   anna memory reset --workspace anna-workspace

初始化
------

.. code-block:: bash

   anna initialize prompt-only anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/prompts/prompt-only.json

   anna initialize full anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/prompts/full.json \
     --workspace anna-workspace

   anna initialize freeze anna-workspace/cases/family_stress_case.json \
     --mode prompt-only \
     --out anna-workspace/prompts/frozen.json \
     --workspace anna-workspace

``prompt-only`` 快，适合冻结单个 prompt。``full`` 会运行完整初始化流水线，可能调用多个模型服务。

运行与日志
----------

.. code-block:: bash

   anna run batch --case "anna-workspace/cases/*.json" \
     --out anna-workspace/runs/batch \
     --mode prompt-only \
     --workspace anna-workspace

   anna logs tail anna-workspace/logs/services/complaint.log --lines 80
   anna cache list --workspace anna-workspace
   anna cache clean --workspace anna-workspace
   anna reset workspace --workspace anna-workspace
