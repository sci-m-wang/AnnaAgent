项目发布与文档站点
==================

本页面面向维护者，说明当前仓库的发布与文档流程。

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
   uv run --group docs sphinx-build -W -b html docs docs/_build/html

PyPI 发布
---------

PyPI 发布不再由 GitHub Actions 自动执行。当前 GitHub workflows 只负责构建和部署文档站点。维护者需要发布新包版本时，请在本地构建 sdist/wheel，并使用维护者自己的 PyPI 发布流程上传。

推荐 tag 与 release 流程：

.. code-block:: bash

   git tag v0.2.0
   git push origin v0.2.0
   gh release create v0.2.0 --title "v0.2.0" --notes "Release v0.2.0"

上传 PyPI 前，请先用 ``uv build`` 在本地验证包，并确认该版本尚未在 PyPI 上存在。

GitHub Pages
------------

文档 workflow 会在 ``main`` 更新时从 ``docs/`` 构建一个 Sphinx 站点。每个页面包含英文和中文内容块，发布后的站点提供语言切换器来控制显示哪种语言。仓库设置中 Pages source 应选择 ``GitHub Actions``。

本地预览文档
------------

.. code-block:: bash

   uv run --group docs sphinx-build -W -b html docs docs/_build/html

然后打开 ``docs/_build/html/index.html``。
