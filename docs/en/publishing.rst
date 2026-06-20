Project Publishing and Documentation
====================================

This page documents the release and documentation workflow for repository maintainers.

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

PyPI publishing is not automated by GitHub Actions. The GitHub workflows only
build and deploy the documentation site. When a maintainer needs to publish a
new package version, build the source and wheel artifacts locally and upload them
using the maintainer's PyPI account and local release tooling.

Recommended tag and release flow:

.. code-block:: bash

   git tag v0.2.0
   git push origin v0.2.0
   gh release create v0.2.0 --title "v0.2.0" --notes "Release v0.2.0"

Before uploading to PyPI, verify the package locally with ``uv build`` and check
that the version is not already present on PyPI.

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
