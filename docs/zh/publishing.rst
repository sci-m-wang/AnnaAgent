项目发布与文档站点
==================

本页面向维护者，说明当前仓库的发布自动化。

版本来源
--------

版本号保存在两个地方：

* ``pyproject.toml`` 的 ``[project].version``。
* ``src/anna_agent/__init__.py`` 中的 ``__version__``。

发布前应同步更新这两个值。

本地构建
--------

.. code-block:: bash

   uv lock --check
   uv build
   ANNA_DOCS_LANGUAGE=en uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html
   ANNA_DOCS_LANGUAGE=zh uv run --group docs sphinx-build -W -b html -c docs docs/zh docs/_build/html/zh

PyPI 发布
---------

仓库包含 PyPI workflow，会构建 sdist/wheel，并通过 GitHub Secret ``PYPI_API_TOKEN`` 发布到 PyPI。token 保存在 GitHub Actions secrets 中，不写入仓库。触发方式是发布 GitHub Release，或手动运行 workflow。

推荐 release 流程：

.. code-block:: bash

   git tag v0.2.0
   git push origin v0.2.0
   gh release create v0.2.0 --title "v0.2.0" --notes "Release v0.2.0"

如果后续迁移到 PyPI Trusted Publishing，可以移除 ``.github/workflows/python-publish.yml`` 中的 token input，并在 PyPI 中配置匹配的 trusted publisher。

GitHub Pages
------------

文档 workflow 会在 ``main`` 更新时分别从 ``docs/en`` 构建英文站点到根路径，从 ``docs/zh`` 构建中文站点到 ``/zh/``，并部署到 GitHub Pages。发布后的站点包含语言切换器。仓库设置中 Pages source 应选择 ``GitHub Actions``。

本地预览文档
------------

.. code-block:: bash

   ANNA_DOCS_LANGUAGE=en uv run --group docs sphinx-build -W -b html -c docs docs/en docs/_build/html
   ANNA_DOCS_LANGUAGE=zh uv run --group docs sphinx-build -W -b html -c docs docs/zh docs/_build/html/zh

然后打开 ``docs/_build/html/index.html``。
