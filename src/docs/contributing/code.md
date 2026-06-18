# 开发者指南

本文档说明如何在本仓库进行开发和贡献代码。本仓库使用 [uv](https://docs.astral.sh/uv/) 管理项目级 `.venv` 环境，并通过 `Makefile` 提供常用的格式化、代码检查和测试命令。

## 代码贡献流程

- 除项目维护者外，请遵循 [fork and pull request](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) 流程进行贡献。
- 提交 PR 前请按照 Pull Request 模板填写相关内容。
- CI 会自动运行 lint 和测试，请在本地确保通过所有检查。
- 如果新增功能或修复 Bug，请同步更新相关文档，并尽可能在 `tests/unit_tests` 或 `tests/integration_tests` 中添加测试。

## 依赖安装

本项目依赖使用 uv 管理。uv 会在仓库根目录创建项目级 `.venv`，不需要手动创建全局或 Conda 环境。先安装 uv：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

在仓库根目录执行以下命令安装开发所需依赖（包含 lint 与测试工具）：

```bash
uv sync --all-groups
```

如果只需要运行 AnnaAgent，不需要开发工具，可以执行：

```bash
uv sync
```

## 常用开发命令

本仓库提供 `Makefile` 方便执行常用任务。以下命令均在仓库根目录运行。

### 代码格式化

使用 [ruff](https://docs.astral.sh/ruff/) 进行格式化：

```bash
make format
```

### 代码检查

运行静态检查和导入检查：

```bash
make lint
```

### 单元测试

运行单元测试：

```bash
make test
```

### 集成测试

运行集成测试：

```bash
make integration_tests
```

### 覆盖率报告

生成覆盖率报告：

```bash
make coverage
```

更多命令可执行 `make help` 查看。
