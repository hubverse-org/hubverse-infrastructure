# Hubverse Infrastructure


<img src="https://www.pulumi.com/images/pricing/team-oss.svg" alt="Pulumi Team edition for open source" style="width:100px; float: left; margin-right: 10px;"/>

This repository uses [Pulumi](https://www.pulumi.com/) to provision cloud resources for the Hubverse, a project that provides open tools for collaborative modeling:
https://hubdocs.readthedocs.io/en/latest/.

## Background

### Hubverse Cloud Integration

At this time, the Hubverse will provide hosting for hubs that opt-in to cloud storage. This may change in the future, but as the Hubverse Cloud work gets started, we want to minimize onboarding friction for hub administrators.

This repository contains the [Pulumi](https://www.pulumi.com/) project that provisions the AWS resources for each cloud-enabled hub hosted on the Hubverse AWS account.


### AWS

At this time, Amazon Web Services (AWS) is the only cloud provider supported by Hubverse hosting.

The code in this repository creates two categories of AWS resources:
1. Resources that are shared across all hubs or are used for Hubverse administration.
2. Resources created specifically for each hub.

#### Shared cloud resources

These resources are created one time for the entire Hubverse:

1. As S3 bucket to store shared files. The contents are not publicly accessible because they are for internal use.
2. An AWS lambda function that transforms model-output files into a standardized format.

#### Hub-specific cloud resources

Each cloud-enabled hub requires several dedicated AWS resources. These resources are created for each hub:

1. An S3 bucket to store data (with public read access).
2. An IAM _role_ that can be assumed by GitHub Actions. This role has two associated _policies_:
    - A _trust policy_ that stipulates the role can only be used by GitHub Actions that originate from the main branch of the hub's repository.
    - A _permission policy_ that grants write access to the hub's S3 bucket.


## Onboarding a Hub

TODO: Add detailed instructions for onboarding a hub to the cloud.
1. Update the `hubs.yaml` file with the hub's name and the desired AWS region.
2.  Submit a pull request

## Dev Setup

The code here uses a simple .yaml file that lists the cloud-enabled hubs. For each hub on the list, the Pulumi entry point invokes a Python function that provisions the required AWS resources.

### Required permissions

This repo uses two GitHub workflows to manage Hubverse AWS resources. Each workflow assumes an IAM role with the permissions it needs (via GitHub's OIDC identity provider).

| GitHub Workflow                                                 | Trigger                | Infrastructure Permissions  |
| --------------------------------------------------------------- | ---------------------- | --------------------------- |
| [`pulumi_preview.yaml`](.github/workflows/pulumi_preview.yaml)  | PR to `main` & ad-hoc  | read-only                   |
| [`pulumi_update.yaml`](.github/workflows/pulumi_update.yaml)    | merge to `main`        | read update create delete   |


If you're a Hubverse developer who wants to use Pulumi locally (using [Pulumi's CLI](https://www.pulumi.com/docs/cli/), for example), you will need access to AWS credentials with the same permissions used by the GitHub workflows.

### Setup instructions

1. Make sure you have the required version on Python installed on your machine (see [`.python-version`](.python-version)).

    **note:** [pyenv](https://github.com/pyenv/pyenv) is a good tool for managing multiple version of Python on a single machine.

2. Clone this repository and navigate to the project directory.

3. Make sure your machine's current Python interpreter is set to the project's required version of Python, and then create a virtual environment. You can use any third-party tool that manages Python environments (e.g., pipenv, poetry), or you can use Python's built-in `venv` module (make sure you're at the top of the project directory):
    ```bash
    python -m venv .venv
    ```

4. Activate the virtual environment. If you created the environment using the `venv` command above, you can activate it as follows:
    ```bash
    source .venv/bin/activate
    ```

5. Install the project's dependencies:
    ```bash
    pip install -r requirements/dev-requirements.txt && pip install -e .
    ```


### Adding dependencies

This project uses `pip-tools` to generate requirements files from `pyproject.toml`.  To add new dependencies, you will need to install [`pip-tools`](https://pip-tools.readthedocs.io/en/latest/) into your virtual environment (or use [`pipx`](https://github.com/pypa/pipx) to make it available on your machine globally).

To add a new dependency:

1. Add dependency to the `dependencies` section `pyproject.toml` (if it's a dev dependency, add it to the `dev` section of `[project.optional-dependencies]`).

2. Regenerate the `requirements.txt` file (you can skip this if you've only added a dev dependency):
    ```bash
    pip-compile --output-file=requirements/requirements.txt pyproject.toml
    ```

3. Regenerate the `requirements-dev.txt` file (you will need to do this every time, even if you haven't added a dev dependency):
    ```bash
    pip-compile --extra=dev --output-file=requirements/dev-requirements.txt pyproject.toml
    ```

4. Install the updated dependencies into your virtual environment:
    ```bash
    pip install -r requirements/dev-requirements.txt
    ```
