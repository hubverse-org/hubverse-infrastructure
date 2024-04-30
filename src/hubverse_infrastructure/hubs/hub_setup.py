"""Code needed to provision AWS resources for a new hub."""

from hubverse_infrastructure.hubs.iam import create_iam_infrastructure
from hubverse_infrastructure.hubs.s3 import create_s3_infrastructure


def set_up_hub(hub_info: dict):
    """
    Create all AWS instrastructure needed for a Hubverse hub.
    For simplicity, this demo uses the hub name as the bucket name,
    though the new cloud section of a hub's admin.json config allows
    a different bucket name.
    """

    hub_bucket = create_s3_infrastructure(hub_info)
    hub_info["hub_bucket"] = hub_bucket
    create_iam_infrastructure(hub_info)
