"""Code needed to provision AWS resources for a new hub."""

from hubs.s3 import create_s3_infrastructure
from hubs.iam import create_iam_infrastructure

def set_up_hub(hub_info:dict):
    '''
    Create all AWS instrastructure needed for a Hubverse hub.
    For simplicity, this demo uses the hub name as the bucket name,
    though the new cloud section of a hub's admin.json config allows
    a different bucket name.
    '''

    create_s3_infrastructure(hub_info)
    create_iam_infrastructure(hub_info)
