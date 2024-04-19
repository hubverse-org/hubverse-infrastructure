"""Create the AWS infrastructure needed to run Hubverse model-output transformations as Lambda functions."""
import io
from zipfile import ZipFile

import boto3
import pulumi
import pulumi_aws as aws
from botocore.exceptions import ClientError
from cloudpathlib import CloudPath
from pulumi import ResourceOptions  # type: ignore


def create_bucket(bucket_name: str) -> aws.s3.BucketV2:
    """
    Create the S3 bucket used to store shared Hubverse assets and give the AWS Lambda service read access to it.
    """

    hubverse_asset_bucket = aws.s3.BucketV2(bucket_name, bucket=bucket_name, tags={"hub": "hubverse"})

    # Create an S3 policy that allows the AWS Lambda service to read from the bucket
    # (this is a permissive read policy because it applies to any lambda function, but the Hubverse
    # deals in open source data and code, so we can leave keep it open for simplicity).
    s3_policy_document = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="ReadAssetBucket",
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectAcl",
                ],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service", identifiers=["lambda.amazonaws.com"]
                    ),
                ],
                resources=[f"arn:aws:s3:::{bucket_name}/*"],
            ),
            aws.iam.GetPolicyDocumentStatementArgs(
                sid="ListAssetBucket",
                actions=[
                    "s3:ListBucket",
                ],
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service", identifiers=["lambda.amazonaws.com"]
                    ),
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


def create_cloudwatch_write_policy(policy_name: str) -> aws.iam.Policy:
    """
    Create a policy that allows write access to AWS CloudWatch logs
    (we'll need to attach this to the Lambda execution role)
    """

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
    """
    Create IAM role that the hubverse-transform lambda will assume and attach the necessary permissions.
    """

    # Because getting ARNs from Pulumi resources is terrible, the code below manually constructs the ARN
    # of the hubverse-transform lambda function. To do that, we need the current AWS account id and its
    # default region.
    aws_account = aws.get_caller_identity().account_id
    aws_region = aws.get_region().name

    # Create the role used by the lambda function, and limit its use to hubverse-transform lambda function
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
                conditions=[
                    aws.iam.GetPolicyDocumentStatementConditionArgs(
                        test="StringEquals",
                        variable="aws:SourceArn",
                        values=[f"arn:aws:lambda:{aws_region}:{aws_account}:function:{lambda_name}"],
                    ),
                ],
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
    lambda_name: str, package_location: CloudPath, lambda_role: aws.iam.Role, hubverse_asset_bucket: aws.s3.BucketV2
) -> aws.lambda_.Function:
    """
    Create the scaffolding for the Lambda function that transforms a model-output file.
    """

    s3_bucket = package_location.drive
    s3_key = package_location.key  # type: ignore

    # Using arn.apply below ensures that the create_lambda_package_placeholder doesn't run
    # until the hubverse_asset_bucket exists (because a bucket's arn isn't available until
    # the bucket has been physically created on AWS).
    hubverse_asset_bucket.arn.apply(lambda _: create_lambda_package_placeholder(s3_bucket, s3_key))

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
        opts=ResourceOptions(depends_on=[hubverse_asset_bucket]),
    )

    return transform_lambda


def create_lambda_package_placeholder(s3_bucket: str, s3_key: str):
    """
    Create a lambda package placeholder in S3 if necessary.
    """

    # if we're in a dry run (such as a Pulumi preview), skip this
    if pulumi.runtime.is_dry_run():
        return

    # This module creates a "scaffolding" lambda, which is designed to run packaged function code
    # stored in an S3 bucket. We don't want Pulumi to manage the lambda's actual code because
    # we don't want the hubverse transform functionality tightly coupled to the Hubverse-managed
    # AWS infrastructure. However, if the code package (which is deployed by the hubverse-transform
    # repo) doesn't exist yet, we need to create a placeholder zip file. It's a chicken-and-egg problem
    # that should only occur until the hubverse-transform deployment pipeline is up and running)

    s3 = boto3.resource("s3")
    lambda_package = s3.Object(s3_bucket, s3_key)
    try:
        lambda_package.get()
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "NoSuchKey":
            placeholder_zip = io.BytesIO()
            zip_file = ZipFile(placeholder_zip, "w")
            zip_file.writestr("placeholder", b"lambda function placeholder")
            zip_file.close()
            placeholder_zip.seek(0)
            lambda_package.put(Body=placeholder_zip)
        else:
            raise Exception(f"Boto error when checking for existing lambda package: {s3_bucket}/{s3_key}") from e
    except Exception as e:
        raise Exception(f"Error when checking for existing lambda package: {s3_bucket}/{s3_key}") from e


def create_transform_infrastructure():
    """
    Create all AWS infrastructure required to support the lambda function that will
    operate on cloud-based model-output files.
    """
    bucket_name = "hubverse-assets"
    lambda_name = "hubverse-transform-model-output"
    lambda_package_location = "s3://hubverse-assets/lambda/hubverse-transform-model-output.zip"
    lambda_package_path = CloudPath(lambda_package_location)

    bucket = create_bucket(bucket_name)
    lambda_role = create_lambda_execution_permissions(lambda_name)
    create_transform_lambda(lambda_name, lambda_package_path, lambda_role, bucket)
