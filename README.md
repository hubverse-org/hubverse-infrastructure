# Hubverse Infrastructure

This repository belongs to the Hubverse, a project that provides open tools for collaborative modeling:
https://hubdocs.readthedocs.io/en/latest/.

## Background

### Hubverse Cloud Integration

At this time, the Hubverse will provide hosting for hubs that opt-in to cloud storage. This may change in the future, but as the Hubverse Cloud work gets started, we want to minimize onboarding friction for hub administrators.

This repository contains the [Pulumi](https://www.pulumi.com/) project that provisions the AWS resources for each cloud-enabled hub hosted on the Hubverse AWS account.


### Supported Cloud Providers

At this time, the Hubverse supports Amazon Web Services (AWS) as a cloud provider.


#### AWS

Each cloud-enabled hub requires the following AWS resources:

1. An S3 bucket to store data (with public read access).
2. An IAM _role_ that can be assumed by GitHub Actions. This role has two associated _policies_:
    - A _trust policy_ that stipulates the role can only be used by GitHub Actions that originate from the main branch of the hub's repository.
    - A _permission policy_ that grants write access to the hub's S3 bucket.

This repository contains two Pulumi-related GitHub workflows create and destroy the above AWS resources as needed:

* `pulumi_preview.yml`: runs when a pull request is opened and reports any related AWS resource changes
* `pulumi_update.yml`: runs when a pull request is merged and applies the AWS changes

The GitHub actions use an OIDC identity provider to authenticate with AWS.

![Github and OIDC](https://docs.github.com/assets/cb-63262/mw-1440/images/help/actions/oidc-architecture.webp)


## Onboarding a Hub

TODO: Add detailed instructions for onboarding a hub to the cloud.
1. Update the `hubs.yaml` file with the hub's name and the desired AWS region.
2.  Submit a pull request

## Dev Setup

The code here uses a simple .yaml file that lists the cloud-enabled hubs. For each hub on the list, the Pulumi entry point invokes a Python function that provisions the required AWS resources.

If you're a Hubverse developer running Pulumi locally, you will need to setup the project, and you will need the required Hubverse AWS credentials.

### Setup instructions

1. Clone this repository and navigate to the project directory

2. Create virtual environment and install dependencies
```bash
conda env create -f environment.yml
```
3. Activate the virtual environment
```bash
conda activate hubverse-infrastructure
```

### Adding dependencies

This project uses `pip-tools` to generate requirements files from `pyproject.toml`. Managing dependencies
this way requires a few more steps than using a tool like PDM, but requirements.txt work better
with Pulumi than tooling-specific lockfiles from utilities like PDM.

To add a new dependency:

1. Add dependency to the `dependencies` section `pyproject.toml` (if it's a dev dependency,
add it to the `dev` section of `[project.optional-dependencies]`).

2. Regenerate the `requirements.txt` file:
```bash
python -m piptools compile -o requirements/requirements.txt pyproject.toml
```

3. If you've added a dev dependency, regenerate the `requirements-dev.txt` file:
```bash
python -m piptools compile --extra dev -o requirements/dev-requirements.txt pyproject.toml
```

4. Update the current environment:
```bash
conda env update -f environment.yml
```
