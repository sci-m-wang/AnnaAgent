案例数据与长期记忆
==================

案例文件结构
------------

AnnaAgent 案例文件可以是 JSON 或 YAML，包含来访者画像、案例报告和历史疗程对话。

主要字段：

``id``
  稳定案例 ID。

``seeker_id``
  稳定来访者 ID，用于长期记忆过滤。

``portrait``
  人口学信息、风险分数、症状和可选元数据。

``report``
  结构化咨询案例报告。公开样例使用中文字段。

``conversation`` 或 ``previous_conversations``
  历史疗程对话，每轮至少包含 ``role`` 和 ``content``。

运行实验前先校验：

.. code-block:: bash

   anna data validate anna-workspace/cases/family_stress_case.json
   anna data inspect anna-workspace/cases/family_stress_case.json

生成样例
--------

.. code-block:: bash

   anna data sample --out anna-workspace/cases/sample.json

可以把生成文件当作格式参考，然后替换为你有伦理许可的数据。

长期记忆
--------

AnnaAgent 使用 LanceDB 存储本地长期记忆。历史对话和报告会切分为多种 memory record：

* ``conversation_turn``
* ``conversation_window``
* ``session_summary``
* ``report_section``
* ``report_summary``

索引案例：

.. code-block:: bash

   anna memory index anna-workspace/cases/family_stress_case.json --workspace anna-workspace

检索记忆：

.. code-block:: bash

   anna memory search "家庭压力和睡眠问题" --workspace anna-workspace

查看或重置记忆：

.. code-block:: bash

   anna memory stats --workspace anna-workspace
   anna memory inspect --workspace anna-workspace
   anna memory reset --workspace anna-workspace

Prompt-Only 与 Full State
-------------------------

``prompt-only`` state 创建很快，会把案例冻结成紧凑 system prompt，适合轻量实验。

``full`` state 会运行完整动态初始化流水线，包含主诉链、状态摘要、近期情境、说话风格分析和最终 seeker system prompt。

入门和批量 smoke test 建议用 ``prompt-only``。需要完整 AnnaAgent 行为时，再使用 ``full`` 并确保模型服务已经配置好。
