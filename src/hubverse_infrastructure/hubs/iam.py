import pulumi
import pulumi_aws as aws


def create_trust_policy(org: str, repo: str):
    """Create the trust policy that will used with the IAM role for Github Actions."""

    # retrieve information about the hubverse account's OIDC github provider
    oidc_github = aws.iam.get_open_id_connect_provider(url="https://token.actions.githubusercontent.com")

    # Create the policy that defines who will be allowed to assume
    # a role using the OIDC provider we create for GitHub Actions.
    # The conditions specify that only Github can assume the role.
    # Furthermore, the role can only be assumed from the hub's repo,
    # and only from the main branch.
    github_policy_document = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=["sts:AssumeRoleWithWebIdentity"],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Federated",
                        # identifiers=[f"arn:aws:iam::{aws.get_caller_identity().account_id}:oidc-provider/token.actions.githubusercontent.com"]
                        identifiers=[oidc_github.arn],
                    )
                ],
                conditions=[
                    aws.iam.GetPolicyDocumentStatementConditionArgs(
                        test="StringEquals",
                        variable=f"{oidc_github.url}:aud",
                        values=["sts.amazonaws.com"],
                    ),
                    aws.iam.GetPolicyDocumentStatementConditionArgs(
                        test="StringEquals",
                        variable=f"{oidc_github.url}:sub",
                        values=[f"repo:{org}/{repo}:ref:refs/heads/main"],
                    ),
                ],
            )
        ]
    )

    return github_policy_document.json


def create_github_role(hub_name: str, policy_document):
    """Create the IAM role that will be assumed by Github Actions."""

    github_role = aws.iam.Role(
        name=hub_name,
        resource_name=hub_name,
        description="The role assumed by CI/CD for writing data to S3.",
        tags={"hub": hub_name},
        assume_role_policy=policy_document,
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
                resources=[f"arn:aws:s3:::{hub_name}"],
            ),
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:GetObject",
                    "s3:GetObjectAcl",
                    "s3:DeleteObject",
                ],
                resources=[f"arn:aws:s3:::{hub_name}/*"],
            ),
        ]
    )

    bucket_write_policy_name = f"{hub_name}-write-bucket-policy"
    bucket_write_policy = aws.iam.Policy(
        name=bucket_write_policy_name,
        resource_name=bucket_write_policy_name,
        description=f"Policy attached to {hub_name} role. It allows writing to the {hub_name} S3 bucket",
        policy=s3_write_policy.json,
        tags={"hub": hub_name},
    )

    return bucket_write_policy


def attach_bucket_write_policy(resource_name: str, role: aws.iam.Role, bucket_write_policy: aws.iam.Policy):
    """Attach the S3 write policy to the role that Github Actions assumes."""

    # Update the role we created for Github Actions by attaching the
    # policy that allows writes to the hub's S3 bucket
    aws.iam.RolePolicyAttachment(resource_name=resource_name, role=role.name, policy_arn=bucket_write_policy.id)


def create_lambda_bucket_write_policy(hub_names: list[str], model_output_lambda_role: aws.iam.Role):
    """Grant the shared transform Lambda write access to every hub bucket.

    There is a single transform Lambda (and a single role it assumes), but it must write
    transformed output back to every hub's bucket. Attaching one managed policy per hub to
    that shared role hits the AWS PoliciesPerRole quota (10 by default, 20 hard max), so
    instead we attach a single inline policy that enumerates all hub buckets explicitly.

    Buckets are enumerated explicitly (not via a wildcard) to keep the Lambda's effective
    permissions identical to a per-hub grant and preserve least privilege. Inline policies
    do not count against the managed-policy PoliciesPerRole quota. See issue #132.
    """

    bucket_arns = [f"arn:aws:s3:::{hub_name}" for hub_name in hub_names]
    object_arns = [f"arn:aws:s3:::{hub_name}/*" for hub_name in hub_names]

    s3_write_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:ListBucket",
                ],
                resources=bucket_arns,
            ),
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:GetObject",
                    "s3:GetObjectAcl",
                    "s3:DeleteObject",
                ],
                resources=object_arns,
            ),
        ]
    )

    policy_name = "hubverse-transform-model-output-write-bucket-policy"
    aws.iam.RolePolicy(
        resource_name=policy_name,
        name=policy_name,
        role=model_output_lambda_role.name,
        policy=s3_write_policy.json,
    )


def create_model_output_lambda_trigger(
    hub_name: str, hub_bucket: aws.s3.Bucket, model_output_lambda: aws.lambda_.Function
) -> aws.s3.BucketNotification:
    """Create the trigger that will invoke the model output lambda when a new file is written to the hub's S3 bucket."""

    allow_bucket = aws.lambda_.Permission(
        resource_name=f"{hub_name}-allow",
        action="lambda:InvokeFunction",
        function=model_output_lambda.arn.apply(lambda arn: f"{arn}"),
        principal="s3.amazonaws.com",
        source_arn=hub_bucket.arn.apply(lambda arn: f"{arn}"),
    )

    bucket_notification = aws.s3.BucketNotification(
        resource_name=f"{hub_name}-create-notification",
        bucket=hub_bucket.id,
        lambda_functions=[
            aws.s3.BucketNotificationLambdaFunctionArgs(
                id=f"{hub_name}-notification-args",
                lambda_function_arn=model_output_lambda.arn.apply(lambda arn: f"{arn}"),
                events=["s3:ObjectCreated:*", "s3:ObjectRemoved:*"],
                filter_prefix="raw/",
            )
        ],
        opts=pulumi.ResourceOptions(depends_on=[allow_bucket]),
    )

    return bucket_notification


def create_iam_infrastructure(hub_info: dict):
    """Create the IAM infrastructure needed for a hub."""
    org = hub_info["org"]
    repo = hub_info["repo"]
    hub = hub_info["hub"]
    hub_bucket = hub_info["hub_bucket"]
    model_output_lambda = hub_info["model_output_lambda"]

    trust_policy = create_trust_policy(org, repo)
    github_role = create_github_role(hub, trust_policy)
    s3_write_policy = create_bucket_write_policy(hub)
    attach_bucket_write_policy(hub, github_role, s3_write_policy)
    create_model_output_lambda_trigger(hub, hub_bucket, model_output_lambda)
