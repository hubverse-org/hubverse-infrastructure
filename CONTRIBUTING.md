# Contributing to hubverse-infrastructure

This document covers how to propose a change to `hubverse-infrastructure` and how to set up the project
for development on your local machine.

This is an internal Hubverse package used to manage cloud infrastructure, so these directions are intended
for the Hubverse development team.

For general info about contributing to Hubverse packages, please see the
[**hubverse contributing guide**](https://docs.hubverse.io/en/latest/overview/contribute.html).

## Onboarding a hub

> [!TIP]
> You do not need to set up a `hubverse-infrastructure` local development
> environment to provision S3 resource for a new hub.

Provisioning AWS resources for a new hub requires adding a few lines to
[`hubs.yaml`](src/hubverse_infrastructure/hubs/hubs.yaml). Thus, Hubverse developers can onboard a new hub by
using the GitHub UI to modify `hubs.yaml` as described in [README.md](README.md#onboarding-a-hub).

## Local development setup

This project uses [`uv`](https://docs.astral.sh/uv/) to manage Python installs,
dependencies, and virtual environments. The result is less work to set up
a development environment.

However, contributors who prefer different Python tools can still use them as
long as dependency updates follow the workflow of adding (or removing)
dependencies from `pyproject.toml` and re-generating an annotated
`requirements/requirements.txt` file. In other words, don't update
the requirements.txt file directly.

> [!IMPORTANT]
> If you have an active Python virtual environment (for example, conda's
> base environment), you'll need to deactivate it before following the
> instructions below.
> See the hubDocs wiki for further
> [troubleshooting information](https://github.com/hubverse-org/hubDocs/wiki/Troubleshooting).

1. Install uv on your machine (you will only need to do this once):
<https://docs.astral.sh/uv/getting-started/installation/>
2. The rest of the instructions should be executed from the cloned repository's root directory
(*e.g.*, `/Users/hubUser/repositories/hubverse-infrastructure`).
3. Create a virtual environment for the project:

    ```bash
    uv venv --seed
    ```

    > [!NOTE]
    > The output of this command provides an instruction for activating the new
    > virtual environment. Doing so is optional, as subsequent `uv` commands
    > will detect and use the environment automatically.

4. Install dependencies (including install the package in editable mode):

    ```bash
    uv pip install -r requirements/requirements.txt
    uv pip install -e .
    ```

5. Run the tests to ensure that everything is working:

    ```bash
    uv run pytest
    ```

Once you've confirmed that the project is set up correctly, make your changes and follow the Hubverse's
[Python development workflow](https://docs.hubverse.io/en/latest/developer/python.html).

### Adding, updating, or removing project dependencies

If you need to update a hubverse-infrastructure dependency:

1. Add, change, or delete the dependency in the project config (`pyproject.toml`):

    ```bash
    uv add <name of package>
    ```

    or

    ```bash
    uv add <name of package> --upgrade
    ```
    or

    ```bash
    uv remove <name of package >
    ```

2. Generate updated requirements files:

    ```script
    uv pip compile pyproject.toml -o requirements/requirements.txt
    uv pip compile pyproject.toml --extra dev -o requirements/dev-requirements.txt
    ```

3. Install the updated requirements into your development environment:

    ```script
    uv pip install -r requirements/dev-requirements.txt
    ```
