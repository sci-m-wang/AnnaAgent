Troubleshooting
===============

Command Not Found
-----------------

If ``anna`` is not available after installation, check the tool directory used by
``uv`` or ``pipx`` and ensure it is on ``PATH``.

.. code-block:: bash

   uv tool list
   pipx list

Configuration Fails
-------------------

Run:

.. code-block:: bash

   anna doctor --workspace anna-workspace
   anna config show --workspace anna-workspace
   anna config validate --workspace anna-workspace

Check that ``settings.yaml`` exists and that secrets are present in ``.env``.

Model Calls Fail
----------------

Verify the base URL, model name, and API key. The endpoint must be compatible
with OpenAI chat completions.

.. code-block:: bash

   anna test model --workspace anna-workspace

Memory Search Fails
-------------------

Check embedding configuration first:

.. code-block:: bash

   anna test embedding --workspace anna-workspace
   anna memory stats --workspace anna-workspace

If the embedding endpoint changed, reset and rebuild the memory index.

vLLM Does Not Start
-------------------

Use a longer wait timeout for large models:

.. code-block:: bash

   anna models deploy --target complaint --backend vllm --workspace anna-workspace \
     --gpu 0 --gpu-memory-utilization 0.85 --wait-timeout 900

If the CLI reports missing CUDA toolkit, confirm that ``nvcc`` is visible or pass
``--cuda-home``. On module-based clusters, AnnaAgent attempts to discover and
load CUDA modules for the child process automatically.

If FlashInfer JIT fails because ``ninja`` is missing, use a workspace deploy
environment. AnnaAgent will install ``ninja`` into that environment when needed.

Stale Logs Are Confusing
------------------------

Each deploy resets the current target service log before starting vLLM. If you
are reading logs manually, make sure you are looking at the target log under the
current workspace, not an older workspace or previous run directory.

PyPI Publish Fails
------------------

The publish workflow uses the GitHub Secret ``PYPI_API_TOKEN``. If publishing
fails, verify that the secret exists, has not expired, and has permission to
upload releases for the ``anna-agent`` PyPI project.
