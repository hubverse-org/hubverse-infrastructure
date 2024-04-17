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


def create_transform_infrastructure():
    bucket_name = "hubverse-assets"
    hubverse_bucket = create_bucket(bucket_name)

    return hubverse_bucket
