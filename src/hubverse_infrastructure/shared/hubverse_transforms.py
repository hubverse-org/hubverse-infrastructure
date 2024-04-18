"""Create the AWS infrastructure needed to run Hubverse model-output transformations as Lambda functions."""
import pulumi_aws as aws
from cloudpathlib import CloudPath
from pulumi import ResourceOptions  # type: ignore


def create_bucket(bucket_name: str) -> aws.s3.Bucket:
    """
    Create the S3 bucket used to store shared Hubverse assets and give the AWS Lambda service read access to it.
    """

    hubverse_asset_bucket = aws.s3.Bucket(bucket_name, bucket=bucket_name, tags={"hub": "hubverse"})

    # Create an S3 policy that allows the AWS Lambda service to read from the bucket
    # (this is a permissive read policy because it applies to any lambda function, but the Hubverse
    # deals in open source data and code, so we can leave keep it open for simplicity)
    s3_policy_document = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="LambdaReadBucket",
                actions=[
                    "s3:GetObject",
                ],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service", identifiers=["lambda.amazonaws.com"]
                    )
                ],
                resources=[f"arn:aws:s3:::{bucket_name}/*"],
            ),
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="LambdaListBucket",
                actions=[
                    "s3:ListBucket",
                ],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service", identifiers=["lambda.amazonaws.com"]
                    )
                ],
                resources=[f"arn:aws:s3:::{bucket_name}"],
            ),
        ]
    )

    # Apply the policy to the bucket.
    aws.s3.BucketPolicy(
        resource_name=f"{bucket_name}-read-bucket-policy",
        bucket=hubverse_asset_bucket.id,
        policy=s3_policy_document.json,
        opts=ResourceOptions(depends_on=[hubverse_asset_bucket]),
    )

    return hubverse_asset_bucket


def create_cloudwatch_write_policy(policy_name: str):
    # Create a policy that allows write access to AWS CloudWatch logs
    # (we'll need to attach this to the Lambda execution role)
    cloudwatch_write_policy_document = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "logs:PutLogEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                ],
                resources=["arn:aws:logs:*:*:*"],
            ),
        ]
    )

    cloudwatch_write_policy_name = policy_name
    cloudwatch_write_policy = aws.iam.Policy(
        name=cloudwatch_write_policy_name,
        resource_name=cloudwatch_write_policy_name,
        description="Policy that allows writing to AWS CloudWatch logs",
        policy=cloudwatch_write_policy_document.json,
        tags={"hub": "hubverse"},
    )

    return cloudwatch_write_policy


def create_lambda_execution_permissions(lambda_name: str) -> aws.iam.Role:
    """Create IAM role that the hubverse-transform lambda will assume and attach the necessary permissions."""

    # Create the role used by the lambda function
    lambda_role_document = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["lambda.amazonaws.com"],
                    )
                ],
                actions=["sts:AssumeRole"],
            )
        ]
    )

    lambda_role = aws.iam.Role(
        name=f"{lambda_name}-role",
        resource_name=f"{lambda_name}-role",
        description="The role assumed by the Lambda that runs the hubverse-transform function",
        assume_role_policy=lambda_role_document.json,
        tags={"hub": "hubverse"},
    )

    # Create a policy that allows writes to AWS CloudWatch logs and attach it to the lambda role
    cloudwatch_write_policy = create_cloudwatch_write_policy("hubverse-cloudwatch-write-policy")
    aws.iam.RolePolicyAttachment(
        resource_name=f"{lambda_name}-cloudwatch-policy", role=lambda_role.name, policy_arn=cloudwatch_write_policy.id
    )

    return lambda_role


def create_transform_lambda(
    lambda_name: str, package_location: CloudPath, lambda_role: aws.iam.Role
) -> aws.lambda_.Function:
    """
    Create the scaffolding for the Lambda function that transforms a model-output file.
    """

    s3_bucket = package_location.drive
    s3_key = package_location.key

    transform_lambda = aws.lambda_.Function(
        name=lambda_name,
        resource_name=lambda_name,
        description="Runs data transforms on Hubverse model-output files",
        role=lambda_role.arn,
        handler="lambda_function.lambda_handler",
        package_type="Zip",
        runtime="python3.12",
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        tags={"hub": "hubverse"},
        timeout=210,
    )

    return transform_lambda


def create_transform_infrastructure():
    bucket_name = "hubverse-assets"
    lambda_name = "hubverse-transform-model-output"
    lambda_package_location = "s3://hubverse-assets/lambda/hubverse-transform.zip"

    lambda_package_path = CloudPath(lambda_package_location)

    create_bucket(bucket_name)
    lambda_role = create_lambda_execution_permissions(lambda_name)
    create_transform_lambda(lambda_name, lambda_package_path, lambda_role)
