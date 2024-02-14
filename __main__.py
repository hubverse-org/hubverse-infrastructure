"""An Python Pulumi program that generates Hubverse resources in AWS."""

import pulumi_aws as aws
import yaml

def get_hubs() -> list[dict]:
    '''Get the list of cloud-enabled hubs.'''
    with open('hubs.yaml', 'r') as file:
        hubs = yaml.safe_load(file).get('hubs')
    return hubs


def set_up_hub(hub_info:dict):
    '''
    Create all AWS instrastructure needed for a Hubverse hub.

    We're using the hub name to name and tag the resources. A hub's
    backend bucket will default to the name 'hubverse-{hubname}' to
    avoid naming conflicts.

    Note that policy creation code references resources by their known
    names rather than using Pulumi arn outputs, as those didn't work
    in the get_policy_document statements.
    '''
    repo = hub_info['repo']
    org = hub_info['org']
    hub = hub_info['hub']

    bucket_name = f'hubverse-{hub}'
    bucket_write_policy_name = f'{hub}-write-bucket-policy'
    bucket_read_policy_name = f'{hub}-read-bucket-policy'
    github_policy_name = f'{hub}-githubaction-policy'
    github_role_name = f"{hub}-githubaction-role"
    tags={'hub': hub}


    # Create an S3 bucket that has versioning enabled and a public read policy
    hub_bucket = aws.s3.Bucket(
        bucket_name,
        bucket=bucket_name,
        versioning=aws.s3.BucketVersioningArgs(
            enabled=True,
        ),
        tags=tags
    )

    # By default, new S3 buckets do not allow public access. Updating
    # those settings will allow us to create a bucket policy for public access.
    hub_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
        resource_name=f'{bucket_name}-public-access-block',
        bucket=hub_bucket.id,
        block_public_acls=True,
        ignore_public_acls=True,
        block_public_policy=False,
        restrict_public_buckets=False
    )

    # Create an S3 policy that allows public read access and
    # attach it to the hub's bucket. 
    s3_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="PublicReadGetObject",
                actions=[
                    "s3:GetObject",
                ],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(type="*", identifiers=["*"])
                ],
                resources=[
                    f'arn:aws:s3:::{bucket_name}/*'
                ],
            ),
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="PublicListBucket",
                actions=[
                    "s3:ListBucket",
                ],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(type="*", identifiers=["*"])
                ],
                resources=[
                    f'arn:aws:s3:::{bucket_name}'
                ],
            )
        ]
    )

    bucket_read_policy = aws.s3.BucketPolicy(
        resource_name=bucket_read_policy_name,
        bucket=hub_bucket.id,
        policy=s3_policy.json
    )

    # Create the policy that defines who will be allowed to assume
    # a role using the OIDC provider we create for GitHub Actions.
    # The conditions specify that only Github can assume the role.
    # Furthermore, the role can only be assumed from the hub's repo,
    # and only from the main branch.
    github_policy_document = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=["sts:AssumeRoleWithWebIdentity"],
                principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Federated",
                    identifiers=[f"arn:aws:iam::{aws.get_caller_identity().account_id}:oidc-provider/token.actions.githubusercontent.com"]
                )],
                conditions=[
                    aws.iam.GetPolicyDocumentStatementConditionArgs(
                       test="StringEquals",
                       variable=oidc_github.url.apply(lambda url: f'{url}:aud'),
                       values=['sts.amazonaws.com']
                    ),
                    aws.iam.GetPolicyDocumentStatementConditionArgs(
                        test="StringEquals",
                        variable=oidc_github.url.apply(lambda url: f'{url}:sub'),
                        values=[f'repo:{org}/{repo}:ref:refs/heads/main']
                    ) 
                ]
            )
        ]
    )

    github_role = aws.iam.Role(
        name=github_role_name,
        resource_name=github_role_name,
        description=f'The role assumed by CI/CD for writing data to S3. Can be assumed only by a Github Action workflow from the main branch of {org}/{repo}',
        tags=tags,
        assume_role_policy=github_policy_document.json
    )

    # Create an S3 policy that allows writing and attach it to
    # the hub's bucket. This policy will later be attached to 
    # the IAM role that will be assumed by Github Actions
    s3_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:PutoObjectAcl",
                ],
                resources=[
                    f'arn:aws:s3:::{bucket_name}',
                    f'arn:aws:s3:::{bucket_name}/*'
                ],
            )
        ]
    )
    
    bucket_write_policy = aws.iam.Policy(
        resource_name=bucket_write_policy_name,
        description=f'Policy attached to {github_role_name}. It allows writing to the {bucket_name} S3 bucket',
        policy=s3_policy.json,
        tags=tags
    )

    # Update the role we created for Github Actions by attaching the
    # policy that allows writes to the hub's S3 bucket
    aws.iam.RolePolicyAttachment(
        resource_name=github_policy_name,
        role=github_role.name,
        policy_arn=bucket_write_policy.id
    )

# Create the OIDC provider
# The thumbprint below was retrieved via AWS console on 2024-01-30
# TODO: find a better place for this (it works, but don't love using
# global variables)
oidc_github = aws.iam.OpenIdConnectProvider(
    "hubverse-github-actions",
    client_id_lists=["sts.amazonaws.com"],
    thumbprint_lists=["1b511abead59c6ce207077c0bf0e0043b1382612"],
    url="https://token.actions.githubusercontent.com",
)

hub_list = get_hubs()
for hub in hub_list:
    set_up_hub(hub)

