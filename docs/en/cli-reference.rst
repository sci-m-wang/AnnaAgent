CLI Reference
=============

The short command is ``anna``. The longer alias ``anna-agent`` is also available.

Global Commands
---------------

.. code-block:: bash

   anna --version
   anna --help
   anna doctor --workspace anna-workspace
   anna create anna-workspace
   anna chat --workspace anna-workspace
   anna demo --workspace anna-workspace

``doctor`` checks the local AnnaAgent installation, workspace settings, and
common runtime requirements. Run it before expensive experiments.

Assets
------

.. code-block:: bash

   anna assets list --workspace anna-workspace
   anna assets download paper --workspace anna-workspace
   anna assets download complaint-sft --workspace anna-workspace
   anna assets download complaint-sft --manifest anna-workspace/assets/anna-assets.json

Always pass ``--workspace`` or ``--manifest`` so downloads go to the intended
workspace. If you omit both, the current directory becomes the workspace.

Models
------

.. code-block:: bash

   anna models use-base --target all --workspace anna-workspace
   anna models use-sft --target complaint --workspace anna-workspace
   anna models status --workspace anna-workspace
   anna models configure --target emotion \
     --base-url http://127.0.0.1:8000/v1 \
     --model-name emotion \
     --workspace anna-workspace

Use ``models deploy`` for local vLLM services. See :doc:`deployment`.

Data
----

.. code-block:: bash

   anna data validate anna-workspace/cases/family_stress_case.json
   anna data inspect anna-workspace/cases/family_stress_case.json
   anna data sample --out anna-workspace/cases/sample.json
   anna data convert input.yaml --out anna-workspace/cases/input.json

Memory
------

.. code-block:: bash

   anna memory index anna-workspace/cases/family_stress_case.json --workspace anna-workspace
   anna memory search "family pressure and sleep" --workspace anna-workspace
   anna memory stats --workspace anna-workspace
   anna memory inspect --workspace anna-workspace
   anna memory reset --workspace anna-workspace

Initialization
--------------

.. code-block:: bash

   anna init prompt-only anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/prompts/prompt-only.json

   anna init full anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/prompts/full.json \
     --workspace anna-workspace

   anna init freeze anna-workspace/cases/family_stress_case.json \
     --mode prompt-only \
     --out anna-workspace/prompts/frozen.json \
     --workspace anna-workspace

``prompt-only`` is fast and uses a single frozen prompt. ``full`` runs the full
AnnaAgent initialization pipeline and may call multiple model services.

Runs and Logs
-------------

.. code-block:: bash

   anna run batch --case "anna-workspace/cases/*.json" \
     --out anna-workspace/runs/batch \
     --mode prompt-only \
     --workspace anna-workspace

   anna logs tail anna-workspace/logs/services/complaint.log --lines 80
   anna cache list --workspace anna-workspace
   anna cache clean --workspace anna-workspace
   anna reset workspace --workspace anna-workspace
