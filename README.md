# Hubverse Infrastructure


<img src="https://www.pulumi.com/images/pricing/team-oss.svg" alt="Pulumi Team edition for open source" style="width:100px; float: left; margin-right: 10px;"/>

This repository uses [Pulumi](https://www.pulumi.com/) to provision cloud resources for the Hubverse, a project that
provides open tools for collaborative modeling: [https://docs.hubverse.io/en/latest/](https://docs.hubverse.io/en/latest/).

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

## Onboarding a hub to AWS

Other than the ability to submit a PR to this repository, no special permissions are required for onboarding a hub to
the Hubverse AWS account.

Note that these instructions are for provisioning a hub's AWS resources.
There are a few other steps to fully onboard a hub to the cloud. Please
see the [Hubverse documentation](https://docs.hubverse.io/en/latest/) for a complete guide.

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

### AWS components

Pulumi manages two types of Hubverse AWS resources:

- Shared: these are used by all hubs
- Hub-specific: these are created once per hub

It's not necessary to understand the details unless you're debugging or developing new features. Expand the
section below for a list of Pulumi resources mapped to their AWS names and a brief description of what each one does.



<details>

**Shared resources**

The following Pulumi resources were created once and are shared across hubs.

| Pulumi resource name                              | AWS name                                              | Type                            | Description
|---------------------------------------------------|------------------------------------------------------|----------------------------------|-------------|
| hubverse-cloudwatch-write-policy                  | arn:aws:iam::767397675902:policy/hubverse-cloudwatch-write-policy | IAM policy | Allows write access to CloudWatch logs.
| hubverse-transform-model-output                   | arn:aws:lambda:us-east-1:767397675902:function:hubverse-transform-model-output | Lambda function | Transforms user-submitted model-output files to parquet format.
| hubverse-transform-model-output-cloudwatch-policy | n/a | RolePolicyAttachment | Attaches hubverse-cloudwatch-write-policy to the hubverse-transform-model-output Lambda.

**Hub-specific resources**

Below is a list of the hub-specific Pulumi resources, using the CDC FluSight Forecast Hub as an example.

<summary>Pulumi <-> AWS mapping and description</summary>

| Pulumi resource name                          | AWS name                                              | Type                            | Description
|-----------------------------------------------|------------------------------------------------------|----------------------------------|-------------|
| cdcepi-flusight-forecast-hub                  | arn:aws:s3:::cdcepi-flusight-forecast-hub            | S3 bucket                        | AWS bucket stores the hub's data/
| cdcepi-flusight-forecast-read-bucket-policy   | n/a                                                  | Bucket policy                    | Allows public read access to the hub's S3 bucket. Attached to the above bucket.
| cdcepi-flusight-forecast-public-access-block  | n/a                                                  | S3 bucket public access block    | Updates AWS default settings that disable public access (required for bucket policy above to work).
| cdcepi-flusight-forecast                      | arn:aws:iam::767397675902:role/cdcepi-flusight-forecast-hub | IAM role                        | An AWS role that is assumed by hub's GitHub actions.
| cdcepi-flusight-forecast-write-bucket-policy  | arn:aws:iam::767397675902:policy/cdcepi-flusight-forecast-hub-write-bucket-policy | IAM policy | A policy that allows write access to the hub's S3 bucket.
| cdcepi-flusight-forecast                      | n/a                                                  | RolePolicyAttachment             | Attaches cdcepi-flusight-forecast-write-bucket-policy to the cdcepi-flusight-forecast IAM role.
| cdcepi-flusight-forecast-create-notification  | cdcepi-flusight-forecast-hub-notification-args       | S3 notification                  | Emits S3 notifications when data in the `/raw` folder of the hub's S3 bucket is updated.
| cdcepi-flusight-forecast-allow                | n/a                                                  | Lambda permission                | Allows above S3 notification to trigger the transform-model-output-lambda function.
| cdcepi-flusight-forecast-transform-model-output-lambda | n/a                                         | RolePolicyAttachment             | Attaches cdcepi-flusight-forecast-write-bucket-policy to hubverse-transform-model-output-role (so lambda function can write transformed data to the hub's S3 bucket).

**Miscellaneous resources**

Additionally, Pulumi manages a catch-all S3 bucket called `hubverse-assets`. This is a bucket for internal use
and is not used by our hosted hubs (for example, the code for the hubverse-transform-model-output Lambda function
is stored here).

</details>

## Permissions

This section provides an overview of the GitHub, Pulumi, and AWS components that enable us to manage infrastructure via
the code in this repository. Additionally, there are instructions for updating those components if necessary. For
example:

- We want to manage a new type of AWS resource via Pulumi and need to update AWS permissions accordingly
- We want to update the configuration of our Pulumi deployments (_e.g._, change the triggering branch, update the
  session duration of Pulumi's temporary AWS credentials)

### Overview

The Hubverse uses [Pulumi's GitHub app](https://www.pulumi.com/docs/iac/using-pulumi/continuous-delivery/github-app/)
to deploy infrastructure changes to AWS. The app is installed on the
[`hubverse-org` GitHub organization](https://github.com/hubverse-org) and currently has access to this repository.
Only a hubverse-org administrator can change the Pulumi GitHub app settings.

The GitHub app initiates a deployment process when:

- A PR is opened against the this repo's `main` branch (for previewing changes)
- A PR is merged into the `main` branch (for applying changes)

These deployments are configured to use the Pulumi OIDC identity provider created in our Hubverse AWS account. The OIDC
provider allows Pulumi to request temporary AWS credentials and assume the following AWS role when performing previews
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

#### Troubleshooting failed Pulumi deployments

Occasionally, a Pulumi deployment fails. These failures generally fall into
one of two categories.

##### AWS resource failures

If a PR instructs Pulumi to do something not allowed by AWS, Pulumi will. An
example is trying to delete an S3 bucket that contains data, or when `hubs.yaml`
specifies an S3 bucket name that already exists.

When this happens, Pulumi will make the changes it can and report errors
for anything that failed. In other words, Pulumi doesn't group requested infrastructure
changes into a single pass/fail group.

You can't re-run a deployment, but there are generally two ways to recover from a failure:

1. Run a [Pulumi update](https://www.pulumi.com/docs/iac/cli/commands/pulumi_up/#pulumi-up):

    - From Pulumi cloud: navigate to the
     [hubverse stack](https://app.pulumi.com/hubverse/hubverse-aws/hubverse).
     From the _Actions_ drop-down, choose _Update_ and then click _Deploy_.
    - Using the [Pulumi CLI](https://www.pulumi.com/docs/iac/cli/):
    run `pulumi up` from the command line.

    This is the best option if the problem can be resolved within AWS itself
    (for example, you need to manually delete S3 contents before offboarding a hub).

2. Update `hubs.yaml` and submit a follow-up PR to this repo.

   This is best option if the issue was caused by a problem in the
   `hubverse-infrastructure` code (like a invalid S3 bucket name).

##### Pulumi authentication failure

Infrequently, a Pulumi deployment triggered by a PR from this repo fails
with a the following error:

```bash
1 $ /pulumi-deploy-executor cache restore --workDir="/deployment" --stackIdentity="hubverse/hubverse-aws/hubverse"
2 Restoring cache for stack hubverse/hubverse-aws/hubverse
3 Error: failed to get runtime: failed to select stack: exit status 255
4 code: 255
5 stdout:
6 stderr: Logging in using access token from PULUMI_ACCESS_TOKEN
7 error: [401] Unauthorized: No credentials provided or are invalid.
```

The root cause is unknown, but the nuclear "turn it off and on again" option is for an administrator of the
`hubverse-org` GitHub organization to uninstall and re-install the Pulumi GitHub app.

This process can be initiated from Pulumi cloud, on the
[Hubverse stack's integrations page](https://app.pulumi.com/hubverse/hubverse-aws/hubverse/settings/integrations).

### Pulumi configuration

The Hubverse has an [open source team edition](https://github.com/pulumi/team-edition-for-open-source/issues/26) of
Pulumi, which gives us access to automated CI/CD deployments and allows us to have a team of up to 10 members.

To view the Hubverse's Pulumi-managed resources, you will need to create a Pulumi account and be added to the Pulumi
hubverse organization by an existing administrator. As a team member, you will have access to:

- `hubverse-aws`: the [Pulumi project](https://www.pulumi.com/docs/iac/concepts/projects/) the corresponds to this
  repository. Project configuration is managed in [`Pulumi.yaml`](Pulumi.yaml).
- `hubverse`: the [Pulumi stack](https://www.pulumi.com/docs/iac/concepts/stacks/) that contains the production
  AWS resources managed by Pulumi. A Pulumi project can contain multiple stacks, but we only use one. Stack settings
  are managed in [`Pulumi.hubverse.yaml`](Pulumi.hubverse.yaml).
- [Pulumi deployments](https://www.pulumi.com/docs/pulumi-cloud/deployments/): events that represent a preview of
  proposed infrastructure updates or a log of completed infrastructure updates. Deployments are triggered by GitHub
  pull requests and merges.

Each Pulumi stack has settings that control deployment behavior. For example:

- `source control settings`: the GitHub repository and branch that trigger deployments (in our case, the `main` branch
  of `hubverse-infrastructure`)
- `GitHub settings`: what actions should trigger a deployment (_e.g._, run a preview when someone opens a PR)
- `Pre-run commands`: commands to run before a deployment (we use these commands to install Python dependencies)
- `OpenID Connect`: identifier (ARN) of the OIDC provider that Pulumi uses to authenticate to AWS

If any of the above changes, you will need to update the `hubverse/hubverse-aws` deployment settings.

### Updating Pulumi's AWS permissions

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

### Pulumi/GitHub integration

The [Hubverse Pulumi stack](https://app.pulumi.com/hubverse/hubverse-aws/hubverse) has an integration configured to
the `hubverse-org` GitHub organization. This integration enables the Pulumi GitHub app to listen for Pulumi events
from this repository (`hubverse-infrastructure`) and trigger subsequence deployments.

## Local development

See [CONTRIBUTING.md](CONTRIBUTING.md) for instructions on setting up a local development environment.
