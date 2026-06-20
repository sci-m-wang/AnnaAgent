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

PyPI publishing is not automated by GitHub Actions. The GitHub workflows only
build and deploy the documentation site. When a maintainer needs to publish a
new package version, build the source and wheel artifacts locally and upload them
using the maintainer's PyPI account and local release tooling.

Recommended tag and release flow:

.. code-block:: bash

   git tag v0.2.1
   git push origin v0.2.1
   gh release create v0.2.1 --title "v0.2.1" --notes "Release v0.2.1"

Before uploading to PyPI, verify the package locally with ``uv build`` and check
that the version is not already present on PyPI.

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
