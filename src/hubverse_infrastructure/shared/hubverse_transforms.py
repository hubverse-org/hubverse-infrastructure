"""Create the AWS infrastructure needed to run Hubverse model-output transformations as Lambda functions."""
import pulumi_aws as aws
from pulumi import ResourceOptions  # type: ignore


def create_bucket(bucket_name: str) -> aws.s3.Bucket:
    """
    Create the S3 bucket used to store shared Hubverse assets and give the AWS Lambda service read access to it.
    """

    hubverse_asset_bucket = aws.s3.Bucket(bucket_name, bucket=bucket_name, tags={"hub": "hubverse"})

    # Create an S3 policy that will the AWS Lambda service to read from the bucket
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


def create_transform_lambda(lambda_name: str, lambda_bucket_name: str) -> aws.lambda_.Function:
    """
    Create the scaffolding for the Lambda function that transforms a model-output file.
    """

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

    transform_lambda = aws.lambda_.Function(
        name=lambda_name,
        resource_name=lambda_name,
        description="Runs data transforms on Hubverse model-output files",
        role=lambda_role.arn,
        handler="lambda_function.lambda_handler",
        package_type="Zip",
        runtime="python3.12",
        s3_bucket=lambda_bucket_name,
        s3_key="lambda/hubverse-transform.zip",
        tags={"hub": "hubverse"},
        timeout=210,
    )

    return transform_lambda


def create_transform_infrastructure():
    bucket_name = "hubverse-assets"
    lambda_name = "hubverse-transform-model-output"

    create_bucket(bucket_name)
    create_transform_lambda(lambda_name, bucket_name)
