故障排查
========

找不到 anna 命令
----------------

如果安装后没有 ``anna``，检查 ``uv`` 或 ``pipx`` 的工具目录是否在 ``PATH`` 中：

.. code-block:: bash

   uv tool list
   pipx list

配置校验失败
------------

运行：

.. code-block:: bash

   anna doctor --workspace anna-workspace
   anna config show --workspace anna-workspace
   anna config validate --workspace anna-workspace

确认 ``settings.yaml`` 存在，且密钥已经写入 ``.env``。

模型调用失败
------------

检查 base URL、model name 和 API key。服务必须兼容 OpenAI chat completions。

.. code-block:: bash

   anna test model --workspace anna-workspace

长期记忆失败
------------

先检查 embedding 配置：

.. code-block:: bash

   anna test embedding --workspace anna-workspace
   anna memory stats --workspace anna-workspace

如果 embedding endpoint 发生变化，建议重置并重建记忆索引。

vLLM 启动失败
-------------

大模型加载较慢时增加等待时间：

.. code-block:: bash

   anna models deploy --target complaint --backend vllm --workspace anna-workspace \
     --gpu 0 --gpu-memory-utilization 0.85 --wait-timeout 900

如果 CLI 提示找不到 CUDA toolkit，确认 ``nvcc`` 可见，或传入 ``--cuda-home``。在 module 集群上，AnnaAgent 会尝试自动发现并为 vLLM 子进程加载 CUDA module。

如果 FlashInfer JIT 因缺少 ``ninja`` 失败，请使用 workspace deploy environment。AnnaAgent 会在需要时把 ``ninja`` 自动安装到该环境。

日志看起来不对应当前运行
------------------------

每次 deploy 都会重置当前 target 的 service log。手动读日志时请确认路径属于当前 workspace，而不是旧 workspace 或历史 run 目录。

PyPI 发布失败
-------------

发布 workflow 使用 Trusted Publishing。请在 PyPI 中确认项目已信任 ``sci-m-wang/AnnaAgent`` 和 workflow 文件 ``publish.yml``。如果 workflow 配置了 environment，PyPI 的 trusted publisher 配置也必须一致。
