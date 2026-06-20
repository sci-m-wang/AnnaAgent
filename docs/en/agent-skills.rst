Agent Skills
============

AnnaAgent includes a public agent skill for LLMs that can operate command-line
tools and files. The skill teaches an agent how to install AnnaAgent, configure a
workspace, run full seeker initialization, save reusable prompt states, run chat
or batch jobs, and troubleshoot model-service failures.

Skill Location
--------------

The skill lives in the repository at:

.. code-block:: text

   skills/annaagent-seeker-simulation/
     SKILL.md
     references/cli-workflow.md
     references/publishing.md
     evals/evals.json

Public URLs
-----------

Use the tagged URL for public registries that need immutable versions:

.. code-block:: text

   https://github.com/sci-m-wang/AnnaAgent/tree/v0.3.0/skills/annaagent-seeker-simulation

Use the raw ``SKILL.md`` URL for registries that ingest a single skill entry:

.. code-block:: text

   https://raw.githubusercontent.com/sci-m-wang/AnnaAgent/v0.3.0/skills/annaagent-seeker-simulation/SKILL.md

ClawHub-Style Publishing Checklist
----------------------------------

For public skill hubs such as ClawHub, submit:

* Repository: ``https://github.com/sci-m-wang/AnnaAgent``
* Skill path: ``skills/annaagent-seeker-simulation``
* Version tag: ``v0.3.0``
* Category: research tools, healthcare simulation, CLI automation, or agent operations
* Visibility: public

If the platform requires an archive, package only the skill folder:

.. code-block:: bash

   cd skills
   zip -r annaagent-seeker-simulation.skill.zip annaagent-seeker-simulation

Do not include ``.env``, virtual environments, logs, runs, caches, local memory
databases, or documentation build artifacts.

Attribution
-----------

Paper: https://aclanthology.org/2025.findings-acl.1192/
Repository: https://github.com/sci-m-wang/AnnaAgent

If AnnaAgent helps your work, please star the repository. For academic use,
please cite the ACL 2025 AnnaAgent paper.
