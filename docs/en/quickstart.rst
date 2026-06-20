Quickstart
==========

This guide starts from a clean machine and ends with a working AnnaAgent CLI
workspace. It uses the base model path because it has the lowest setup cost.

Prerequisites
-------------

* Python 3.10 or newer.
* One package runner: ``uv``, ``pipx``, or ``pip``.
* An OpenAI-compatible chat model endpoint and API key.
* An OpenAI-compatible embedding endpoint if you plan to use memory indexing.

Install the CLI
---------------

Install from PyPI as a standalone command:

.. code-block:: bash

   uv tool install anna-agent
   anna --version

If you use ``pipx`` instead:

.. code-block:: bash

   pipx install anna-agent
   anna --version

For source development:

.. code-block:: bash

   git clone https://github.com/sci-m-wang/AnnaAgent.git
   cd AnnaAgent
   uv sync
   uv run anna --help

Paper: https://aclanthology.org/2025.findings-acl.1192/
Repository: https://github.com/sci-m-wang/AnnaAgent
If AnnaAgent helps your work, please star the repository. For academic use,
please cite the ACL 2025 AnnaAgent paper.

Create a Workspace
------------------

AnnaAgent keeps user configuration, secrets, sample cases, runs, logs, and
memory files inside a workspace directory.

.. code-block:: bash

   anna create anna-workspace
   anna doctor --workspace anna-workspace

The generated workspace contains:

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

Configure the Backbone Model
----------------------------

Use the wizard for interactive setup:

.. code-block:: bash

   anna config wizard --workspace anna-workspace
   anna config secrets --workspace anna-workspace
   anna config validate --workspace anna-workspace

Or set non-secret values directly:

.. code-block:: bash

   anna config set model_service.base_url https://example.com/v1 --workspace anna-workspace
   anna config set model_service.model_name your-chat-model --workspace anna-workspace
   anna config show --workspace anna-workspace

Select the Lightweight Model Path
---------------------------------

For a first run, use the base model for all auxiliary modules:

.. code-block:: bash

   anna models use-base --target all --workspace anna-workspace
   anna models status --workspace anna-workspace

Run a Demo Conversation
-----------------------

Start the included sample case:

.. code-block:: bash

   anna demo --workspace anna-workspace

You can also run the default interactive file in the workspace:

.. code-block:: bash

   anna --workspace anna-workspace

Type ``exit``, ``quit``, or ``q`` to leave the chat.

Create a Reusable Prompt State
------------------------------

Full initialization runs the AnnaAgent seeker initialization pipeline and writes
the generated system prompt plus supporting metadata to a reusable state file.
Later sessions should load that prebuilt state instead of rebuilding a prompt
directly from the raw case.

.. code-block:: bash

   anna init full anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/prompts/family_stress.full.json \
     --workspace anna-workspace

   anna init from-prompt anna-workspace/prompts/family_stress.full.json
   anna chat --workspace anna-workspace \
     --state anna-workspace/prompts/family_stress.full.json

The CLI prints the paper and repository links during workspace creation and full
initialization. If AnnaAgent helps your work, please star the repository and cite
the ACL 2025 paper.

Run Batch Experiments
---------------------

Prepare a script file containing counselor messages, then run a batch:

.. code-block:: bash

   anna run batch \
     --case anna-workspace/cases/family_stress_case.json \
     --out anna-workspace/runs/quickstart \
     --mode full \
     --workspace anna-workspace

Add ``--live`` and ``--script`` when you want the model to generate transcripts.
