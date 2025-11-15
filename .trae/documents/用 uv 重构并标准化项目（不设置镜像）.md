## 目标
- 采用 uv + PEP 621 管理依赖与运行，替代 Poetry 本地开发流程。
- 保持现有功能与测试无回归，精简并规范目录结构。
- 不设置任何镜像，默认使用 PyPI（国外服务器）。

## 依赖与配置
- 保留 `[project]`、`[project.scripts]`、`[dependency-groups]`，以 PEP 621 描述依赖与分组。
- 移除清华镜像：删除 `pyproject.toml:179-182` 的 `[[tool.uv.index]]` 配置，使用默认 PyPI。
- 保留 `[tool.uv] default-groups = ["dev", "lint", "test"]` 以便 `uv sync` 自动安装本地开发依赖（如需可改为手动 `uv sync --group ...`）。
- 后续阶段移除 Poetry 专属段落（`[tool.poetry.*]` 与 `build-system` 指向 poetry），全面切换到标准构建后端（例如 `hatchling` 或 `setuptools`），当前过渡期先不影响现有使用。

## 目录与代码
- 包内模块：维持 `src/anna_agent/*` 为主包目录；将游离模块收纳到包内，已在 `src/anna_agent/fixed_ms_patient.py`。
- API 组织（建议）：将顶层 `api_server.py` 移至 `src/anna_agent/api/main.py`，并通过 `uv run -- uvicorn anna_agent.api.main:app --port 8080` 启动；修正所有引用为包路径。
- 前端目录（可选）：将 `fronted/` 更名为 `frontend/`，同步更新文档指令与任何脚本引用。

## 工具链与脚本
- Makefile 使用 `uv run --` 执行工具：
  - `make format` → `uv run -- ruff format src tests`
  - `make lint` → `uv run -- ruff check src tests`（保留现有 shell 检查脚本）
  - `make test`、`make coverage`、`make integration_tests` → `uv run -- pytest ...`
- `.gitignore` 保留 `uv.lock`、`.venv`、`node_modules` 忽略项，避免污染仓库。

## 运行与验证
- 安装与同步：`uv sync`（默认安装 dev、lint、test 分组）
- 本地安装包：`uv pip install -e .`
- 运行 CLI：`uv run -- anna-agent demo`
- 启动 API：
  - 过渡版：`uv run -- python api_server.py`
  - 规范版（调整后）：`uv run -- uvicorn anna_agent.api.main:app --host 0.0.0.0 --port 8080`
- 测试：
  - 单元测试：`uv run -- pytest tests/unit_tests`
  - 集成测试：`uv run -- pytest tests/integration_tests`

## CI（后续）
- GitHub Actions 使用 `uv` 安装与缓存：
  - `uv sync`、`uv run -- pytest`
  - 缓存 `.venv` 与 uv 的全局缓存目录以加速构建。

## 迁移步骤（执行顺序）
1. 移除 `pyproject.toml:179-182` 的镜像配置，回到默认 PyPI。
2. 保持现有 PEP 621 段落与 `dependency-groups`，使用 `uv sync` 验证安装。
3. 用 `uv run --` 验证 `make format`、`make lint`、`make test`、`make coverage`。
4. 将 `api_server.py` 收纳到包内并提供 `uvicorn` 启动入口（如需）。
5. （可选）重命名 `fronted/` → `frontend/` 并更新文档。
6. （后续）逐步移除 Poetry 段落与构建后端，转为标准后端，确保打包与发布一致。

## 回滚与兼容
- 如需使用 Poetry，保留的 `poetry.*` 段落仍可工作；`uv` 与 Poetry 在过渡期可并存。
- 所有变更限于配置与入口组织，不改动核心业务逻辑；若出现问题可通过 Git 回滚对应文件。