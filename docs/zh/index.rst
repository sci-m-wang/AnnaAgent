中文文档
========

AnnaAgent 是论文 ``AnnaAgent: Dynamic Evolution Agent System with Multi-Session
Memory for Realistic Seeker Simulation`` 的核心工具包实现。当前仓库聚焦于核心
agent runtime、命令行工具、本地 workspace、长期记忆、模型配置和可选的
vLLM/SFT 部署流程。

你可以用它做什么
----------------

* 从 PyPI 安装 ``anna`` 命令行工具。
* 创建隔离 workspace，保存配置、密钥、案例、日志和运行产物。
* 用 prompt-only 模式快速生成 frozen prompt state。
* 用 full 模式运行包含情绪、主诉链、量表和记忆模块的完整初始化。
* 使用基础 OpenAI-compatible 模型，或接入本地/远程 SFT endpoint。
* 下载论文释放的资产，并在 GPU 机器上用 vLLM 启动 SFT 服务。
* 将历史疗程写入 LanceDB 长期记忆并检索。
* 批量生成实验状态和对话记录，便于复现实验。

推荐阅读顺序
------------

1. :doc:`quickstart`：最快跑通路径。
2. :doc:`configuration`：理解 workspace、配置和密钥。
3. :doc:`cli-reference`：常用命令分组。
4. :doc:`deployment`：需要本地 SFT/vLLM 时阅读。
5. :doc:`data-memory`：案例格式与长期记忆。
6. :doc:`troubleshooting`：排查常见错误。

伦理边界
--------

AnnaAgent 用于研究和模拟，不应被当成临床建议工具，也不应替代专业心理服务。公开仓库不包含受限的真实咨询原始记录，请不要在 issue、日志或公开 prompt 中粘贴敏感咨询数据。

.. toctree::
   :maxdepth: 2
   :caption: 目录

   quickstart
   configuration
   cli-reference
   deployment
   data-memory
   publishing
   troubleshooting
