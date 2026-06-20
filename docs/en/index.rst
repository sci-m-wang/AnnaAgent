English Documentation
=====================

AnnaAgent provides a reusable core toolkit for the paper ``AnnaAgent: Dynamic
Evolution Agent System with Multi-Session Memory for Realistic Seeker
Simulation``. The current repository focuses on the core agent runtime, command
line interface, local workspace format, memory indexing, model configuration,
and optional vLLM-based SFT deployment.

What You Can Do
---------------

* Install ``anna`` as a terminal command from PyPI.
* Create an isolated AnnaAgent workspace with sample cases and configuration.
* Run full seeker initialization with emotion, complaint-chain, scale, and memory modules.
* Save and reload initialized prompt states for later chat sessions.
* Use base OpenAI-compatible models or local SFT endpoints.
* Download released assets and deploy local SFT models with vLLM on GPU machines.
* Index previous sessions into LanceDB and retrieve long-term memory.
* Build batch experiment states and transcripts for reproducible evaluation.

Recommended Reading Order
-------------------------

1. :doc:`quickstart` for the shortest working path.
2. :doc:`configuration` to understand workspaces and secrets.
3. :doc:`cli-reference` for the main command groups.
4. :doc:`deployment` if you need local SFT/vLLM services.
5. :doc:`data-memory` for case files and LanceDB memory.
6. :doc:`troubleshooting` when a command fails.

Ethical Scope
-------------

AnnaAgent is intended for research and simulation. Do not present generated
outputs as clinical advice, do not use the simulator to replace professional
care, and do not attempt to reconstruct restricted real counseling records from
released artifacts.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   quickstart
   configuration
   cli-reference
   deployment
   data-memory
   publishing
   troubleshooting
