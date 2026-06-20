Configuration
=============

AnnaAgent separates project code from runtime state. The repository contains the
package, while each workspace contains configuration, secrets, generated states,
logs, and memory indexes.

Workspace Files
---------------

``settings.yaml``
  Non-secret configuration such as base URLs, model names, feature flags, SFT
  endpoint settings, memory settings, and asset metadata.

``.env``
  Local secrets such as API keys. This file must not be committed.

``.env.example``
  Commented placeholders showing which environment variables can be used.

``assets/anna-assets.json``
  Manifest for HuggingFace repositories, direct-download assets, and local SFT
  model targets.

``cases/``
  JSON or YAML case files used by CLI commands and batch runs.

``prompts/``
  Frozen prompt states and full initialization states.

``runs/`` and ``logs/``
  Experiment outputs, vLLM service PIDs, and service logs.

Inspect and Edit Configuration
------------------------------

.. code-block:: bash

   anna config show --workspace anna-workspace
   anna config show --no-redact --workspace anna-workspace
   anna config set model_service.base_url https://example.com/v1 --workspace anna-workspace
   anna config validate --workspace anna-workspace

Use ``--no-redact`` only on a trusted terminal because it can reveal local
configuration values. API keys should be entered through ``anna config secrets``
or stored in ``.env``.

Model Modes
-----------

AnnaAgent has three practical model modes.

Backbone/base model mode
  The simplest mode. AnnaAgent internal modules call the configured backbone chat
  model. This model can temporarily stand in when no external counselor is wired,
  but formal runs should use a dedicated counselor process or model for counselor
  turns.

Configured SFT endpoint mode
  Use this when complaint-chain or emotion SFT models are already deployed as
  OpenAI-compatible services.

Local vLLM deployment mode
  Use this on Linux/GPU machines when AnnaAgent should start the SFT services for
  you and write the resulting endpoint configuration back to the workspace.

Common commands:

.. code-block:: bash

   anna models use-base --target all --workspace anna-workspace
   anna models use-sft --target all --workspace anna-workspace
   anna models status --workspace anna-workspace

   anna models configure --target complaint \
     --base-url http://127.0.0.1:8001/v1 \
     --model-name complaint \
     --workspace anna-workspace

Secrets and Safety
------------------

* Keep ``.env`` out of Git.
* Prefer environment variables or ``anna config secrets`` for API keys.
* Use redacted output in issue reports and logs.
* Do not paste real counseling records into public issues or model prompts.
