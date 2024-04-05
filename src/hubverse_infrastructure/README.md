# IaC Experiment 1: Pulumi

This directory contains a working prototype for using [Pulumi](https://www.pulumi.com/) to provision the AWS resources needed to onboard a Hubverse hub to the cloud.

Like other tools in this space, Pulumi has a learning curve. One of its appeals is the ability declaratively manage infrastructure using a familiar programming language like Python, rather than using a domain-specific language (DSL) like Terraform's HCL.


## Goals

Ideally, the IaC tool we use for the Hubverse will meet the following criteria:

1. Provide a reasonably easy-to-understand process for onboarding a hub to the cloud (every IaC tool has a learning curve, however).
2. Use a declarative approach to managing infrastructure.
3. Report on the difference bewteen infrastructure as described in our code and the actual state of our cloud resources, so changes can be reviewed before they're applied (_i.e._, provide "state management")
3. Provide CI/CD tools that display the above diffs and automatically update cloud infrastructure when chnages are merged.


## Using Pulumi

This prototype uses a simple .yaml file that lists the cloud-enabled hubs. For each hub on the list, we'll invoke a Python function that uses Pulumi to provision the required AWS resources (in a production environment,
we'd interact with Pulumi via CI/CD).

During the prototype phase, you'll need admin credentials to the Hubverse AWS account for this to work.

1. Join the [Hubverse team on Pulumi](https://app.pulumi.com/hubverse).
2 Install the Pulumi CLI: https://www.pulumi.com/docs/get-started/install/.
3. Verify that Pulumi is installed correctly:
    ```
    pulumi version
    ```
4. Configure Pulumi's access to AWS: https://www.pulumi.com/docs/clouds/aws/get-started/begin/#configure-pulumi-to-access-your-aws-account.
5. Clone this repo and navigate to the `pulumi` directory.
6. Verify that you have access to the Hubverse Pulumi "stack":
    ```
    pulumi stack ls
    ```


## Next Steps

Because this is a prototype, the process isn't production-ready. Potential next steps would be:

- CI/CD integration
- Moving the "stack" from single-user mode to a team
- Adding tests
- Would it make sense to create a "stack" for each hub?