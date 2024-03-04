import pulumi_aws as aws


def create_trust_policy(org: str, repo: str):
    """Create the trust policy that will used with the IAM role for Github Actions."""

    # retrieve information about the hubverse account's OIDC github provider
    oidc_github = aws.iam.get_open_id_connect_provider(url='https://token.actions.githubusercontent.com')

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
                    #identifiers=[f"arn:aws:iam::{aws.get_caller_identity().account_id}:oidc-provider/token.actions.githubusercontent.com"]
                    identifiers=[oidc_github.arn]
                )],
                conditions=[
                    aws.iam.GetPolicyDocumentStatementConditionArgs(
                       test="StringEquals",
                       variable=f'{oidc_github.url}:aud',
                       values=['sts.amazonaws.com']
                    ),
                    aws.iam.GetPolicyDocumentStatementConditionArgs(
                        test="StringEquals",
                        variable=f'{oidc_github.url}:sub',
                        values=[f'repo:{org}/{repo}:ref:refs/heads/main']
                    ) 
                ]
            )
        ]
    )

    return github_policy_document.json


def create_github_role(hub_name: str, policy_document):
    """Create the IAM role that will be assumed by Github Actions."""

    github_role = aws.iam.Role(
        name=hub_name,
        resource_name=hub_name,
        description='The role assumed by CI/CD for writing data to S3.',
        tags={'hub': hub_name},
        assume_role_policy=policy_document
    )

    return github_role


def create_bucket_write_policy(hub_name: str):

    # Create a policy that allows put operations to the hub's
    # S3 bucket. This will then be attached to the IAM role that
    # GitHub actions assumes.
    s3_write_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:ListBucket",
                ],
                resources=[
                    f'arn:aws:s3:::{hub_name}'
                ],
            ),
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                ],
                resources=[
                    f'arn:aws:s3:::{hub_name}/*'
                ],
            )
        ]
    )

    bucket_write_policy_name = f'{hub_name}-write-bucket-policy'
    bucket_write_policy = aws.iam.Policy(
        name=bucket_write_policy_name,
        resource_name=bucket_write_policy_name,
        description=f'Policy attached to {hub_name} role. It allows writing to the {hub_name} S3 bucket',
        policy=s3_write_policy.json,
        tags={'hub': hub_name},
    )

    return bucket_write_policy

def attach_bucket_write_policy(hub_name: str, github_role, bucket_write_policy):
    """Attach the S3 write policy to the role that Github Actions assumes."""

    # Update the role we created for Github Actions by attaching the
    # policy that allows writes to the hub's S3 bucket
    aws.iam.RolePolicyAttachment(
        resource_name=hub_name,
        role=github_role.name,
        policy_arn=bucket_write_policy.id
    )

def create_iam_infrastructure(hub_info: dict):
    """Create the IAM infrastructure needed for a hub."""
    org = hub_info['org']
    repo = hub_info['repo']
    hub = hub_info['hub']
    trust_policy = create_trust_policy(org, repo)
    github_role = create_github_role(hub, trust_policy)
    s3_write_policy = create_bucket_write_policy(hub)
    attach_bucket_write_policy(hub, github_role, s3_write_policy)
