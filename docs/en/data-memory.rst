Case Data and Memory
====================

Case File Shape
---------------

AnnaAgent case files are JSON or YAML documents containing a seeker profile,
case report, and previous-session dialogue history.

Required high-level fields:

``id``
  Stable case identifier.

``seeker_id``
  Stable seeker identifier used for memory filtering.

``portrait``
  Demographic attributes, risk scores, symptoms, and optional metadata.

``report``
  Structured counseling case report. The public sample uses Chinese report keys.

``conversation`` or ``previous_conversations``
  Previous-session turns. Each turn should include ``role`` and ``content``.

Validate a file before running experiments:

.. code-block:: bash

   anna data validate anna-workspace/cases/family_stress_case.json
   anna data inspect anna-workspace/cases/family_stress_case.json

Create a Sample
---------------

.. code-block:: bash

   anna data sample --out anna-workspace/cases/sample.json

Use the generated sample as a format reference, then replace the fictional
content with your own ethically permitted data.

Long-Term Memory
----------------

AnnaAgent uses LanceDB for local long-term memory. Previous conversations and
reports are chunked into memory records such as:

* ``conversation_turn``
* ``conversation_window``
* ``session_summary``
* ``report_section``
* ``report_summary``

Index a case:

.. code-block:: bash

   anna memory index anna-workspace/cases/family_stress_case.json --workspace anna-workspace

Search memory:

.. code-block:: bash

   anna memory search "pressure from family and poor sleep" --workspace anna-workspace

Inspect or reset memory:

.. code-block:: bash

   anna memory stats --workspace anna-workspace
   anna memory inspect --workspace anna-workspace
   anna memory reset --workspace anna-workspace

Reusable Prompt State
---------------------

``full`` states run the complete dynamic initialization pipeline. They include
the generated complaint chain, status summary, sampled situation, style analysis,
and the final seeker system prompt. Save this state when you want to reuse the
initialized seeker later with ``anna chat --state`` or the service API.

AnnaAgent does not support a shortcut that builds a prompt directly from a raw
case without running initialization, because that bypasses the seeker simulation
modules and produces the wrong prompt format.
