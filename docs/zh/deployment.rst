本地 SFT 与 vLLM 部署
=====================

AnnaAgent 可以只使用 base model，但论文系统还包含情绪推断和主诉链生成 SFT 模块。本页说明如何下载资产并在 GPU 机器上部署本地 vLLM 服务。

什么时候需要本路径
------------------

适合以下情况：

* 你有 Linux GPU 机器或集群节点。
* 你希望 AnnaAgent 自动启动 OpenAI-compatible SFT endpoint。
* 你希望部署日志、PID 和 endpoint 配置都由 workspace 管理。

如果只是快速跑样例，或者没有 GPU，继续使用 base model 模式即可。

创建部署环境
------------

推荐将轻量 ``anna`` CLI 和较重的 vLLM runtime 隔离：

.. code-block:: bash

   anna init anna-workspace --deploy-env

   # 或者后续补建：
   anna models env setup --workspace anna-workspace
   anna models env status --workspace anna-workspace

部署环境位于 ``anna-workspace/.anna-deploy-venv``。存在该环境时，``anna models deploy`` 会优先使用其中的 vLLM。

下载释放资产
------------

.. code-block:: bash

   anna assets list --workspace anna-workspace
   anna assets pull paper --workspace anna-workspace

默认 paper preset 包括 emotion SFT、chief complaint chain SFT 和合成数据资源。

启动服务
--------

部署 complaint 模型：

.. code-block:: bash

   anna models deploy --target complaint --backend vllm --workspace anna-workspace \
     --gpu 0 --gpu-memory-utilization 0.85 --wait-timeout 900

部署 emotion 模型：

.. code-block:: bash

   anna models deploy --target emotion --backend vllm --workspace anna-workspace \
     --gpu 1 --gpu-memory-utilization 0.85 --wait-timeout 900

如果只有一张 GPU，请分开部署或降低显存使用率。

CLI 会检查什么
--------------

启动 vLLM 前，AnnaAgent 会检查：

* ``nvidia-smi`` 是否可用。
* 指定 GPU ID 是否存在。
* 剩余显存和 vLLM 显存上限。
* CUDA toolkit 是否能从 ``--cuda-home``、``CUDA_HOME``、``PATH``、常见 CUDA root 或集群 module 中找到。
* FlashInfer JIT 所需的 ``ninja`` 是否可用。

如果 workspace 部署环境缺少 ``ninja``，AnnaAgent 会在启动 vLLM 前自动安装。自动 CUDA module 加载只影响 vLLM 子进程，不会污染用户 shell。

自定义 CUDA 或 vLLM 路径
------------------------

只有 CUDA 安装在特殊位置时才需要 ``--cuda-home``：

.. code-block:: bash

   anna models deploy --target complaint --backend vllm --workspace anna-workspace \
     --gpu 0 --cuda-home /path/to/cuda --gpu-memory-utilization 0.85

如果集群已经提供 vLLM：

.. code-block:: bash

   anna models deploy --target complaint --workspace anna-workspace \
     --vllm-command /path/to/vllm

失败行为
--------

如果服务启动失败或 readiness 超时，AnnaAgent 会打印服务日志尾部，并且不会把坏 endpoint 写入 ``settings.yaml``。日志和 PID 位于 workspace 的 ``logs/services/`` 与 ``runs/services/``。

查看状态：

.. code-block:: bash

   anna models status --workspace anna-workspace
   anna logs tail anna-workspace/logs/services/complaint.log --lines 120
