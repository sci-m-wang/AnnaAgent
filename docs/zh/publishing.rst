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
   uv run --group docs sphinx-build -b html docs docs/_build/html

PyPI 发布
---------

仓库包含 PyPI workflow，会构建 sdist/wheel，并通过 PyPI Trusted Publishing 发布。触发方式是发布 GitHub Release，或手动运行 workflow。

推荐 release 流程：

.. code-block:: bash

   git tag v0.2.0
   git push origin v0.2.0
   gh release create v0.2.0 --title "v0.2.0" --notes "Release v0.2.0"

PyPI 项目需要在 Trusted Publisher 设置中信任本 GitHub 仓库、workflow 文件和可选 environment 名称。仓库中不保存 PyPI token。

GitHub Pages
------------

文档 workflow 会在 ``main`` 更新时从 ``docs/`` 构建 Sphinx HTML，并部署到 GitHub Pages。仓库设置中 Pages source 应选择 ``GitHub Actions``。

本地预览文档
------------

.. code-block:: bash

   uv run --group docs sphinx-build -b html docs docs/_build/html

然后打开 ``docs/_build/html/index.html``。
