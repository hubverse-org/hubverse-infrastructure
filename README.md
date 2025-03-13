# Hubverse Infrastructure


<img src="https://www.pulumi.com/images/pricing/team-oss.svg" alt="Pulumi Team edition for open source" style="width:100px; float: left; margin-right: 10px;"/>

This repository uses [Pulumi](https://www.pulumi.com/) to provision cloud resources for the Hubverse, a project that
provides open tools for collaborative modeling: [https://hubverse.io/en/latest/](https://hubverse.io/en/latest/).

## Background

### Hubverse cloud integration

At this time, the Hubverse is able to provide hosting for hubs that are interested in mirroring their data on the cloud.
Specifically, we can provision the required Amazon Web Services (AWS) resources and provide hub administrators with a
GitHub action that will securely sync their model output, target data, and configuration files to a designated S3 bucket.

The `hubverse-infrastructure` repository contains the [Pulumi](https://www.pulumi.com/)-based infrastructure-as-code
project that manages hub-supporting AWS components.

The code here uses a YAML file that lists the cloud-enabled hubs.
For each hub listed in the file, the Pulumi entry point invokes a Python function that provisions the required
AWS resources.

### AWS

Amazon Web Services (AWS) is the only cloud provider supported by Hubverse hosting.

The code in this repository creates two categories of AWS resources:

1. Resources that are shared across all hubs or are used for Hubverse administration.
2. Resources created specifically for each hub.

#### Shared cloud resources

These resources are created one time for the entire Hubverse:

1. As S3 bucket to store shared files. The contents are not publicly accessible because they are for internal use.
2. An AWS lambda function that transforms model-output files into a standardized format.

#### Hub-specific cloud resources

Each cloud-enabled hub requires several dedicated AWS resources. These resources are created for each hub:

1. An S3 bucket to store data. Hubverse S3 buckets:
   - are versioned
   - allow anonymous public read access to contents
   - have a CORS policy that allows http access to bucket contents
2. An IAM _role_ that can be assumed by GitHub Actions. This role has two associated _policies_:
    - A _trust policy_ that stipulates the role can only be used by GitHub Actions originating from the main branch
      of the hub's repository.
    - A _permission policy_ that grants write access to the hub's S3 bucket.

## Onboarding a hub

To begin syncing an existing Hubverse hub to S3:

1. Add a new `hub` entry to [`hubs.yaml`](src/hubverse_infrastructure/hubs/hubs.yaml):
    - `hub` key: the name of the hub (this value will be used as the S3 bucket name, so make sure it's something unique)
    - `org`:  the GitHub organization that hosts the hub's repository
    - `repo`: the name of the hub's repository

    For example:

    ```yaml
    - hub: flusight-forecast
      org: cdcepi
      repo: FluSight-forecast-hub
    ```

2. Submit the above changes as a pull request (PR) to this repository.
3. Shortly after the PR is opened, Pulumi will add a comment about the AWS changes it will make once the PR is merged.

    For example:

    ```bash
        Name                                             Type                                                Operation
    +   flusight-forecast                                aws:iam/role:Role                                      create
    +   flusight-forecast-write-bucket-policy            aws:iam/policy:Policy                                  create
    +   flusight-forecast-allow                          aws:lambda/permission:Permission                       create
    +   flusight-forecast-transform-model-output-lambda  aws:iam/rolePolicyAttachment:RolePolicyAttachment      create
    +   flusight-forecast                                aws:s3/bucket:Bucket                                   create
    +   flusight-forecast-read-bucket-policy             aws:s3/bucketPolicy:BucketPolicy                       create
    +   flusight-forecast                                aws:iam/rolePolicyAttachment:RolePolicyAttachment      create
    +   flusight-forecast-public-access-block            aws:s3/bucketPublicAccessBlock:BucketPublicAccessBlock create
    +   flusight-forecast-create-notification            aws:s3/bucketNotification:BucketNotification           create
    ```

4. If the Pulumi preview looks good, the PR can be merged after a code review. Once the PR is merged, Pulumi will apply
   the AWS changes.
5. The hub is now hosted in the Hubverse AWS account.

> [!IMPORTANT]
> The value of `hub` in `hubs.yaml` must match the value of `cloud.host.storage_location` in the hub's `admin.json`
> configuration file. The `org` and `repo` fields are used to create permissions that allow the hub's GitHub workflow
> to sync data to s3. If these values are not correct, the workflow will fail.

## Permissions

The Hubverse uses Pulumi's GitHub app to deploy infrastructure changes to AWS. The GitHub app initiates a deployment
process when:

- A PR is opened against the this repo's `main` branch (for previewing changes)
- A PR is merged into the `main` branch (for applying changes)

These deployments are configured to use the Pulumi OIDC identity provider created in our Hubverse AWS account. The OIDC
provider allows Pulumi to request temporary AWS credentials and assume the following AWS role when peforming previews
and updates:

- `hubverse-infrastructure-write-role`

The combination of Pulumi's GitHub app and the Pulumi OIDC identity provider in the Hubverse AWS account means that
this repository does not need to store any secrets or tokens to initiate infrastructure changes.

```mermaid
%%{init: {
    "theme": "neutral",
    "themeVariables": {
        "lineColor": "#0077b6",
        "primaryColor": "#ade8f4",
        "secondaryColor": "#48cae4",
        "primaryBorderColor": "#0096c7",
        "secondaryBorderColor": "#0096c7"
    }
}}%%
graph TD
A[hubverse-infrastructure: pull request or merge to main] --> B[Pulumi GitHub App]
B --> C[Pulumi]
C -->|AWS authentication via Pulumi OIDC provider| D[Pulumi OIDC provider]
D -->|temporary AWS access token| C[Pulumi]
C -->|assume AWS role| E[hubverse-infrastructure-write-role]
C -->|preview and perform AWS updates| F[hub AWS resources]

subgraph Hubverse AWS
    D
    E
    F
end
```

### Updating permissions used by Pulumi

If a Pulumi deployment returns a 403 error, it's likely the Pulumi code is trying to make a change that the AWS IAM
`hubverse-infrastructure-write-role` role doesn't have permission to make.

`hubverse-infrastructure-write-role` is attached to an IAM policy that describes what it's allowed to do:

- `hubverse-infrastructure-write-policy`.

The hubverse-infrastructure role and policies are managed outside of Pulumi. Thus, to grant additional permissions
required for Pulumi operations, you will need to update `hubverse-infrastructure-write-policy` via the AWS console:

1. Log in to the AWS console.
2. Click on _Services_ in the top left corner, and then click on _IAM_.
3. From the _IAM_ dashboard, find the _Access management_ section in the left-hand menu and click on _Policies_.
4. When the list of policies appears, use the search box to find `hubverse-infrastructure-write-policy` and click on it.
5. Click the _Edit_ button to update the policy.

> [!IMPORTANT]
> To make these changes, you will need a Hubverse AWS login with:
>
> - console permission
> - policy update permissions

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
