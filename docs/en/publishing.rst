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
   rm -rf docs/_build/gettext docs/_build/html
   uv run --group docs sphinx-build -W -b gettext -c docs docs/en docs/_build/gettext
   uv run python docs/tools/check_i18n.py docs/_build/gettext docs/locale/zh_CN/LC_MESSAGES
   ANNA_DOCS_LANGUAGE=en uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html
   ANNA_DOCS_LANGUAGE=zh_CN uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html/zh

PyPI Publishing
---------------

PyPI publishing is automated by ``.github/workflows/python-publish.yml``. The
workflow runs when a GitHub Release is published and can also be started manually
from GitHub Actions. It builds the source distribution and wheel with
``uv build``, then uploads them with PyPI Trusted Publishing, so the workflow
does not use a ``PYPI_API_TOKEN`` secret.

For Trusted Publishing to work, configure the PyPI project publisher to trust
this repository and workflow path:

.. code-block:: text

   owner: sci-m-wang
   repository: AnnaAgent
   workflow: python-publish.yml
   environment: (leave empty unless the workflow is changed to use one)

Recommended tag and release flow:

.. code-block:: bash

   git tag v0.3.1
   git push origin v0.3.1
   gh release create v0.3.1 --title "v0.3.1" --notes "Release v0.3.1"

After the release is created, GitHub Actions publishes the package automatically.
Before creating the release, verify the package locally with ``uv build`` and
check that the version is not already present on PyPI.

GitHub Pages
------------

The documentation workflow uses the Sphinx i18n/gettext pipeline. English source
files live under ``docs/en``. Chinese translations live under
``docs/locale/zh_CN/LC_MESSAGES``. The workflow first rebuilds gettext catalogs,
checks that the Chinese catalogs are synchronized, then deploys English pages at
the site root and Chinese pages under ``/zh/``. In the repository settings,
Pages should use ``GitHub Actions`` as the source.

Local Documentation Preview
---------------------------

.. code-block:: bash

   rm -rf docs/_build/gettext docs/_build/html
   uv run --group docs sphinx-build -W -b gettext -c docs docs/en docs/_build/gettext
   uv run python docs/tools/check_i18n.py docs/_build/gettext docs/locale/zh_CN/LC_MESSAGES
   ANNA_DOCS_LANGUAGE=en uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html
   ANNA_DOCS_LANGUAGE=zh_CN uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html/zh

Then open ``docs/_build/html/index.html`` or ``docs/_build/html/zh/index.html``
in a browser.
