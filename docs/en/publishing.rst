Project Publishing and Documentation
====================================

This page documents the release automation configured for repository maintainers.

Version Source
--------------

The package version is stored in two places:

* ``pyproject.toml`` under ``[project].version``.
* ``src/anna_agent/__init__.py`` as ``__version__``.

Both values should be updated together before a release.

Build Locally
-------------

.. code-block:: bash

   uv lock --check
   uv build
   uv run --group docs sphinx-build -b html docs docs/_build/html

PyPI Publishing
---------------

The repository includes a PyPI workflow that builds source and wheel artifacts
and publishes them with PyPI Trusted Publishing. The workflow is triggered by a
published GitHub Release or by manual ``workflow_dispatch``.

Recommended release flow:

.. code-block:: bash

   git tag v0.2.0
   git push origin v0.2.0
   gh release create v0.2.0 --title "v0.2.0" --notes "Release v0.2.0"

The PyPI project must trust this GitHub repository, workflow file, and optional
environment name in the PyPI publishing settings. No PyPI token is stored in the
repository.

GitHub Pages
------------

The documentation workflow builds Sphinx HTML from ``docs/`` and deploys it to
GitHub Pages whenever ``main`` changes. In the repository settings, Pages should
use ``GitHub Actions`` as the source.

Local Documentation Preview
---------------------------

.. code-block:: bash

   uv run --group docs sphinx-build -b html docs docs/_build/html

Then open ``docs/_build/html/index.html`` in a browser.
