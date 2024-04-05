"""An Python Pulumi program that generates Hubverse resources in AWS."""

import yaml

from hubs.hub_setup import set_up_hub


def get_hubs() -> list[dict]:
    """Get the list of cloud-enabled hubs."""
    with open("hubs/hubs.yaml", "r") as file:
        hubs = yaml.safe_load(file).get("hubs")
    return hubs


hub_list = get_hubs()
for hub in hub_list:
    set_up_hub(hub)
