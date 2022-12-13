import asyncio
import config
import pandas as pd
from tabulate import tabulate
import meraki
import meraki.aio

# Instantiate async Meraki API client
aiomeraki = meraki.aio.AsyncDashboardAPI(
            config.api_key,
            base_url="https://api.meraki.com/api/v1",
            log_file_prefix=__file__[:-3],
            print_console=False,
            maximum_retries=config.max_retries,
            maximum_concurrent_requests=config.max_requests,
)

# Instantiate synchronous Meraki API client
dashboard = meraki.DashboardAPI(
    config.api_key,
    base_url="https://api.meraki.com/api/v1",
    log_file_prefix=__file__[:-3],
    print_console=config.console_logging,
    )

async def get_network_template_quality_profiles(aiomeraki, net_id):
    """
    Async function wrapper for switch access policies
    :param aiomeraki: Async Dashboard API client
    :param net_id: network ID of target network
    :return: Access policies belonging to this network ID
    """
    results = await aiomeraki.camera.getNetworkCameraQualityRetentionProfiles(net_id)
    results = [result for result in results if 'qp-' in result['name']]
    return net_id, "quality_profiles", results

async def get_network_template_wireless_profiles(aiomeraki, net_id):
    """
    Async function wrapper for switch port schedules
    :param aiomeraki: Async Dashboard API client
    :param net_id: network ID of target network
    :return: Port Schedules belonging to this network ID
    """
    results = await aiomeraki.camera.getNetworkCameraWirelessProfiles(net_id)
    results = [result for result in results if 'wp-' in result['name']]
    return net_id, "wireless_profiles", results

async def get_network_template_alerts(aiomeraki, net_id):
    """
    Async function wrapper for switch access policies
    :param aiomeraki: Async Dashboard API client
    :param net_id: network ID of target network
    :return: Access policies belonging to this network ID
    """
    results = await aiomeraki.networks.getNetworkAlertsSettings(net_id)
    return net_id, "cam_alerts", results

async def get_target_network_data(aiomeraki, target_networks):
    """
    Obtains existing configs on target networks using async functions
    :param aiomeraki: Async Dashboard API client
    :param target_networks: List containing all target networks
    :return: net_attributes: Dictionary with all of the networks as keys, and values are subdictionaries containing
    each of the network parameters.
    """
    net_attributes = {}
    # Build list of async functions to call
    get_tasks = []
    for network in target_networks:
        get_tasks.append(get_network_template_quality_profiles(aiomeraki, network['id']))
        get_tasks.append(get_network_template_wireless_profiles(aiomeraki, network['id']))
        get_tasks.append(get_network_template_alerts(aiomeraki, network['id']))

    # Await and sort
    for task in asyncio.as_completed(get_tasks):
        net_id, action, result = await task
        if net_id not in net_attributes.keys():
            net_attributes[net_id] = {}
        net_attributes[net_id][action] = result

    return net_attributes

async def gather_camera_specific_data(aiomeraki):
    """
    Gathers the information necessary to propagate switch configs from the source template specified in the config.py
    file.
    :param aiomeraki: asyncio instance of the Dashboard API client with access to the source and target organizations,
    as well as the source configuration templates
    :returns: target_devices: List of dicts containing each of the switches to be updated across the whole organization.
             target_networks: List of dicts containing each of the networks with switches to be updated across the
             whole organization.
             temp_switch_profiles: List of dicts containing each of the switch profiles in the source configuration
             template.
             temp_switch_profile_ports: List of dicts with each of the existing ports in the switch profile in the
             source configuration template.
             temp_access_policies: List of dicts with each of the access policies existing in the source configuration
             template.
             temp_port_schedules: List of dicts with each of the port schedules existing in the source configuration
             template.
             net_attributes: Dict containing a Key for every Network to be updated including their existing Access
             Policies and Port Schedules.
             target_switch_ports: List of dicts containing each of the switches to be updated along with the ports to
             update in each one.
    """
    # Get list of MV devices in the organization with the tag specified in config.dst_cam_tag
    org_devices = await aiomeraki.organizations.getOrganizationDevices(
        organizationId=config.src_org_id,
        tags=[config.dst_camera_tag],
        model='MV',
        total_pages=-1
    )

    # Obtain list of networks in the organization with the config.dst_network_tag
    org_networks = await aiomeraki.organizations.getOrganizationNetworks(
        organizationId=config.src_org_id,
        tags=[config.dst_network_tag],
        total_pages=-1
    )

    # Obtain src_quality_profiles, src_wireless_profiles and src_camera_alerts
    src_quality_profiles, src_wireless_profiles, src_camera_alerts = await gather_template_network_data(aiomeraki)

    # Obtain set of networks those MV devices are mapped to
    device_nets = [*set(d['networkId'] for d in org_devices)]

    # Construct a set of the network IDs of said networks
    tagged_nets = [*set(net['id'] for net in org_networks)]
    # Find intersection between set of networks tagged MS devices belong to, and tagged networks
    definitive_nets = list(set(device_nets)&set(tagged_nets))
    # Filter list of MV with definitive network list
    target_devices = [dev for dev in org_devices if dev['networkId'] in definitive_nets]
    # Obtain list of serial numbers from definitive MV list
    target_device_serials = [dev['serial'] for dev in target_devices]
    # Filter list of tagged networks with the network IDs in definitive_nets
    target_networks = [net for net in org_networks if net['id'] in definitive_nets]

    if config.verbose==True:
        print("Target Devices:")
        print(tabulate(pd.DataFrame(target_devices), headers='keys', tablefmt ='fancy_grid'))
        print("Target Networks:")
        print(tabulate(pd.DataFrame(target_networks), headers='keys', tablefmt='fancy_grid'))

    # Build dictionary with target networks as keys, and access policies and port schedules as subkeys
    net_attributes = await get_target_network_data(aiomeraki, target_networks)

    if config.verbose == True:
        for key in net_attributes.keys():
            print(f"Quality Profiles currently in Network {key}:")
            print(tabulate(pd.DataFrame(net_attributes[key]['quality_profiles']), headers='keys', tablefmt='fancy_grid'))
            print(f"Wireless Profiles currently in Network {key}:")
            print(tabulate(pd.DataFrame(net_attributes[key]['wireless_profiles']), headers='keys', tablefmt='fancy_grid'))


    return target_devices, target_networks, src_quality_profiles, src_wireless_profiles, src_camera_alerts, net_attributes

async def gather_template_network_data(aiomeraki):
    """
    Gathers the information necessary to propagate switch configs from the source network specified in the config.py
    file.
    :param aiomeraki: asyncio instance of the Dashboard API client with access to the source and target organizations,
    as well as the source configuration templates
    :returns: src_quality_profiles: List of quality profiles in the source network
              src_wireless_profiles: List of wireless profiles in the source network
              src_camera_alerts: List of alerts in the source network
    """
    # Network attributes to be obtained from template
    get_tasks = [
        get_network_template_quality_profiles(aiomeraki, config.src_net_id),
        get_network_template_wireless_profiles(aiomeraki, config.src_net_id),
        get_network_template_alerts(aiomeraki, config.src_net_id),
    ]

    # Await and sort
    for task in asyncio.as_completed(get_tasks):
        net_id, action, result = await task
        if action=='quality_profiles':
            src_quality_profiles = result
        elif action=='wireless_profiles':
            src_wireless_profiles = result
        elif action=='cam_alerts':
            src_camera_alerts = result

    if config.verbose==True:
        print("Source Template Camera Quality Profiles:")
        try:
            print(tabulate(pd.DataFrame(src_quality_profiles), headers='keys', tablefmt='fancy_grid'))
        except:
            print("No Quality Profiles Found!")
        print("Source Template Camera Wireless Profiles:")
        try:
            print(tabulate(pd.DataFrame(src_wireless_profiles), headers='keys', tablefmt='fancy_grid'))
        except:
            print("No Wireless Profiles Found!")
        print("Source Template Camera Alerts:")
        try:
            print(tabulate(pd.DataFrame(src_camera_alerts["alerts"]), headers='keys', tablefmt='fancy_grid'))
        except:
            print("No Camera Alerts Found!")

    return src_quality_profiles, src_wireless_profiles, src_camera_alerts


async def main(aiomeraki):
    async with aiomeraki:
        target_devices, target_networks, src_quality_profiles, src_wireless_profiles, src_camera_alerts, net_attributes \
            = await gather_camera_specific_data(aiomeraki)

    return target_devices, target_networks, src_quality_profiles, src_wireless_profiles, src_camera_alerts, net_attributes
