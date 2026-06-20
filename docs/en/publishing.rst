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
   uv run --group docs sphinx-build -W -b html docs docs/_build/html

PyPI Publishing
---------------

The repository includes a PyPI workflow that builds source and wheel artifacts
and publishes them with the ``PYPI_API_TOKEN`` GitHub Secret. The token is kept
in GitHub Actions secrets and is not stored in the repository. The workflow is
triggered by a published GitHub Release or by manual ``workflow_dispatch``.

Recommended release flow:

.. code-block:: bash

   git tag v0.2.0
   git push origin v0.2.0
   gh release create v0.2.0 --title "v0.2.0" --notes "Release v0.2.0"

If the project later migrates to PyPI Trusted Publishing, remove the token input
from ``.github/workflows/python-publish.yml`` and configure the matching trusted
publisher in PyPI.

GitHub Pages
------------

The documentation workflow builds one Sphinx site from ``docs/``. Each page
contains English and Chinese content blocks, and the published site includes a
language switcher that controls which language is visible. In the repository
settings, Pages should use ``GitHub Actions`` as the source.

Local Documentation Preview
---------------------------

.. code-block:: bash

   uv run --group docs sphinx-build -W -b html docs docs/_build/html

Then open ``docs/_build/html/index.html`` in a browser.
