Local SFT and vLLM Deployment
=============================

AnnaAgent can use base models only, but the paper system also uses SFT modules
for emotion inference and chief-complaint chain generation. This page explains
how to download released assets and deploy local vLLM services.

When to Use This Path
---------------------

Use local deployment when:

* You have a Linux GPU machine or cluster node.
* You want AnnaAgent to start OpenAI-compatible SFT endpoints for you.
* You want reproducible service logs and workspace-managed endpoint settings.

Stay on base model mode when you only need to run a quick example or do not have
GPU access.

Create the Deploy Environment
-----------------------------

The recommended setup keeps the lightweight ``anna`` CLI separate from the heavy
vLLM runtime environment.

.. code-block:: bash

   anna init anna-workspace --deploy-env

   # Or add it later:
   anna models env setup --workspace anna-workspace
   anna models env status --workspace anna-workspace

The deploy environment is stored at ``anna-workspace/.anna-deploy-venv``. When
it exists, ``anna models deploy`` automatically uses the vLLM executable inside
that environment.

Download Released Assets
------------------------

.. code-block:: bash

   anna assets list --workspace anna-workspace
   anna assets pull paper --workspace anna-workspace

The default paper preset includes the emotion inference SFT model, the chief
complaint chain SFT model, and released synthetic data resources.

Deploy Services
---------------

Deploy the complaint model:

.. code-block:: bash

   anna models deploy --target complaint --backend vllm --workspace anna-workspace \
     --gpu 0 --gpu-memory-utilization 0.85 --wait-timeout 900

Deploy the emotion model:

.. code-block:: bash

   anna models deploy --target emotion --backend vllm --workspace anna-workspace \
     --gpu 1 --gpu-memory-utilization 0.85 --wait-timeout 900

If you have one GPU, deploy one target at a time or lower memory utilization.

What the CLI Checks
-------------------

Before starting vLLM, AnnaAgent checks:

* ``nvidia-smi`` availability.
* Whether the requested GPU ID exists.
* Free GPU memory and the requested vLLM memory cap.
* CUDA toolkit visibility through ``--cuda-home``, ``CUDA_HOME``, ``PATH``, common CUDA roots, or cluster modules.
* ``ninja`` availability for FlashInfer JIT builds.

If a workspace deploy environment is missing ``ninja``, AnnaAgent installs it
into that environment before starting vLLM. CUDA module loading affects only the
vLLM child process and does not modify the user's shell.

Custom CUDA or vLLM Paths
-------------------------

Use ``--cuda-home`` only when CUDA is installed in a custom location:

.. code-block:: bash

   anna models deploy --target complaint --backend vllm --workspace anna-workspace \
     --gpu 0 --cuda-home /path/to/cuda --gpu-memory-utilization 0.85

Use ``--vllm-command`` when your cluster already provides vLLM:

.. code-block:: bash

   anna models deploy --target complaint --workspace anna-workspace \
     --vllm-command /path/to/vllm

Failure Behavior
----------------

If startup fails or the readiness check times out, AnnaAgent prints the service
log tail and does not write a bad endpoint into ``settings.yaml``. Logs and PIDs
are stored under ``logs/services/`` and ``runs/services/`` inside the workspace.

Check the status after deployment:

.. code-block:: bash

   anna models status --workspace anna-workspace
   anna logs tail anna-workspace/logs/services/complaint.log --lines 120
