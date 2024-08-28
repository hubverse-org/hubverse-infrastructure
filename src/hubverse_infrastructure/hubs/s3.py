import pulumi_aws as aws
from pulumi import ResourceOptions  # type: ignore


def create_bucket(hub_name: str) -> aws.s3.Bucket:
    """
    Create a new S3 bucket for a hub.
    (for simplicity, in this demo we're setting the bucket name to the hub name)
    """

    hub_bucket = aws.s3.Bucket(hub_name, bucket=hub_name, tags={"hub": hub_name})

    return hub_bucket


def make_bucket_public(bucket: aws.s3.Bucket, bucket_name: str):
    """
    Make the specified S3 bucket public.
    Note that we're passing in the bucket_name rather than derviving it from the
    Pulumi object, because doing so is a complete nightmare and not well-supported
    in their Python SDK.
    """

    # By default, new S3 buckets do not allow public access. Updating
    # those settings will allow us to create a bucket policy for public access.
    hub_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
        resource_name=f"{bucket_name}-public-access-block",
        bucket=bucket.id,
        block_public_acls=True,
        ignore_public_acls=True,
        block_public_policy=False,
        restrict_public_buckets=False,
    )

    # Create an S3 policy that allows public read access.
    s3_policy = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="PublicReadGetObject",
                actions=[
                    "s3:GetObject",
                ],
                principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(type="*", identifiers=["*"])],
                resources=[f"arn:aws:s3:::{bucket_name}/*"],
            ),
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="PublicListBucket",
                actions=[
                    "s3:ListBucket",
                ],
                principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(type="*", identifiers=["*"])],
                resources=[f"arn:aws:s3:::{bucket_name}"],
            ),
        ]
    )

    # Apply the public read policy to the bucket.
    aws.s3.BucketPolicy(
        resource_name=f"{bucket_name}-read-bucket-policy",
        bucket=bucket.id,
        policy=s3_policy.json,
        # The dependency below ensures that the bucket's public access block has
        # already been updated to allow public access. Otherwise, trying to
        # apply the "everyone can read" policy will throw a 403.
        opts=ResourceOptions(depends_on=[hub_bucket_public_access_block]),
    )


def add_s3_cors_config(bucket: aws.s3.Bucket, bucket_name: str):
    """
    Add CORS configuration to a specified S3 bucket.
    Having a CORS policy allows S3 buckets to be accessed via HTTP requests.
    """

    aws.s3.BucketCorsConfigurationV2(
        resource_name=f"{bucket_name}-bucket-cors-config",
        bucket=bucket.id,
        cors_rules=[
            {
                "allowed_headers": ["*"],
                "allowed_methods": [
                    "GET",
                    "HEAD",
                ],
                "allowed_origins": ["*"],
                "expose_headers": [],
                "max_age_seconds": 3000,
            }
        ],
    )


def create_s3_infrastructure(hub_info: dict) -> aws.s3.Bucket:
    hub_name = hub_info["hub"]
    bucket = create_bucket(hub_name)
    make_bucket_public(bucket, hub_name)
    add_s3_cors_config(bucket, hub_name)
    return bucket
