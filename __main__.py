"""An Python Pulumi program that generates Hubverse resources in AWS."""

import pulumi_aws as aws


# Create the OIDC provider
# The thumbprint below was retrieved via AWS console on 2024-01-30
default = aws.iam.OpenIdConnectProvider(
    "github-actions",
    client_id_lists=["sts.amazonaws.com"],
    thumbprint_lists=["1b511abead59c6ce207077c0bf0e0043b1382612"],
    url="https://token.actions.githubusercontent.com",
)

