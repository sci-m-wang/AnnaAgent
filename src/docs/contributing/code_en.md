# Developer Guide

This document describes how to develop and contribute code to this repository. The project uses [Poetry](https://python-poetry.org/) to manage dependencies and provides a `Makefile` with common formatting, linting and testing commands.

## Contribution Workflow

- Except for maintainers, please follow the [fork and pull request](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) workflow.
- Fill in the Pull Request template before submitting.
- Continuous integration will run lint and tests automatically. Make sure all checks pass locally.
- When adding features or fixing bugs, update the documentation accordingly and add tests in `tests/unit_tests` or `tests/integration_tests` whenever possible.

## Dependency Installation

The project dependencies are managed with Poetry. If you are using Conda, it is recommended to create and activate a new environment first:

```bash
conda create -n annaagent python=3.10
conda activate annaagent
```

Install Poetry following its [official guide](https://python-poetry.org/docs/#installing-with-pipx). After installation, if you use Conda or Pyenv, run:

```bash
poetry config virtualenvs.prefer-active-python true
```

Then install all development dependencies (including lint and test tools) from the repository root:

```bash
poetry install --with lint,test
```

## Common Development Commands

The repository provides a `Makefile` to easily run common tasks. All commands are executed from the project root.

### Code Formatting

Use [ruff](https://docs.astral.sh/ruff/) to format the code:

```bash
make format
```

### Linting

Run static and import checks:

```bash
make lint
```

### Unit Tests

Run the unit tests:

```bash
make test
```

### Integration Tests

Run the integration tests:

```bash
make integration_tests
```

### Coverage Report

Generate a coverage report:

```bash
make coverage
```

Run `make help` for more commands.
