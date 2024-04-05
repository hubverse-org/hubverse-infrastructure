# Hubverse Infrastructure

This repository contains the code needed to provision cloud resources for Hubverse hubs that would like
to store their data in the cloud.

## Hubverse Cloud Integration

At this time, the Hubverse will provide hosting for hubs that opt-in to cloud storage. This may change in the future, but as the Hubverse Cloud work gets started, we want to minimize onboarding friction for hub administrators.

This repository contains the [Pulumi](https://www.pulumi.com/) project that provisions the AWS resources for each cloud-enabled hub hosted on the Hubverse AWS account.


## Supported Cloud Providers

At this time, the Hubverse supports Amazon Web Services (AWS) as a cloud provider.


### AWS

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

If you're a Hubverse developer running Pulumi locally, you will need to setup the projectm and you will need the required Hubverse AWS credentials.

TODO: Add detailed project setup instructions.
