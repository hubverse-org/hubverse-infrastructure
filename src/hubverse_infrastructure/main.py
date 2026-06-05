"""An Python Pulumi program that generates Hubverse resources in AWS."""

import yaml

from hubverse_infrastructure.hubs.hub_setup import set_up_hub
from hubverse_infrastructure.hubs.iam import create_lambda_bucket_write_policy
from hubverse_infrastructure.shared.hubverse_transforms import create_transform_infrastructure

# First, create infrastructure components that are shared across hubs.
model_output_lambda, model_output_lambda_role = create_transform_infrastructure()


# Then, create hub-specific infrastructure.
def get_hubs() -> list[dict]:
    """Get the list of cloud-enabled hubs."""
    with open("hubs/hubs.yaml", "r") as file:
        hubs = yaml.safe_load(file).get("hubs")
    return hubs


hub_list = get_hubs()
for hub in hub_list:
    hub["model_output_lambda"] = model_output_lambda
    set_up_hub(hub)

# Grant the shared transform Lambda write access to every hub bucket via a single inline
# policy on its role, rather than one managed-policy attachment per hub (which exhausts the
# AWS PoliciesPerRole quota). See issue #132.
create_lambda_bucket_write_policy([hub["hub"] for hub in hub_list], model_output_lambda_role)
