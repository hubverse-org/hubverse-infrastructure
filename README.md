# Hubverse Infrastructure

**WIP Status**

This repository contains the code needed to provision cloud resources for Hubverse hubs that would like
to store their data in the cloud.

Hubs that opt-in to Hubverse Cloud should expect the following during the initial phase of this project:

- The data submission process will not change.
- Whenever a pull request is merged into the hub repository's main branch, a GitHub Action workflow will
   sync data from the following hub folders to an S3 bucket:
    - hub-config
    - model-metadata
    - model-output
- Each hub will have its own S3 bucket, and the data will stored there will be publicly available (read-only).
- Existing Hubverse clients for accessing data (_e.g._, `hubUtils`) will be able to read data from the S3 bucket.

## Supported Cloud Providers

At this time, the Hubverse supports AWS. To minimize friction for hub administrators, the Huberverse will
provide hosting for the required AWS infrastructure. This may change in the future.

Hubs that store data on the cloud will use a GitHub Action workflow that accesses the relevant S3 bucket. 
To provide this access without storing secrets in Hubverse repositories, we've chosen to use OpenID Connect (OIDC) for authentication.

It's not important for Hubverse admins to know the details of OIDC, but below is a high-level overview of how it works. Essentially, Github will request temporary credentials from AWS. AWS will grant these credentials if the request is signed correctly and originates from the main branch of the correct repo.

Creating one S3 bucket per hub, along with the corresponding permissions, ensures that we can provide hub-specific AWS permissions and prevent hubs from inadvertnetly overwriting each other's data.

![Github and OIDC](https://docs.github.com/assets/cb-63262/mw-1440/images/help/actions/oidc-architecture.webp)

## Infrastructure as Code

Because we're provisioning cloud resources per-hub, it's important to manage these resources in a way that allows for source control, reviews, and audits. In other words, we want to treat our cloud resources as code.

We haven't yet made a final decision on the Infrastructure as Code (IaC) tool we'll use. At this time, we have a working prototype that uses Pulumi. More information about how to use it can be found in [Pulumi](pulumi).