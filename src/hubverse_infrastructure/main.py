"""An Python Pulumi program that generates Hubverse resources in AWS."""

import yaml

from hubverse_infrastructure.hubs.hub_setup import set_up_hub
from hubverse_infrastructure.shared.hubverse_transforms import create_transform_infrastructure

# First, create infrastructure components that are shared across hubs.
model_output_lambda_role = create_transform_infrastructure()


# Then, create hub-specific infrastructure.
def get_hubs() -> list[dict]:
    """Get the list of cloud-enabled hubs."""
    with open("hubs/hubs.yaml", "r") as file:
        hubs = yaml.safe_load(file).get("hubs")
    return hubs


hub_list = get_hubs()
for hub in hub_list:
    hub["model_output_lambda_role"] = model_output_lambda_role
    set_up_hub(hub)
