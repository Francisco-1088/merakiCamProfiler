import config
import read_functions
import write_functions
from tabulate import tabulate
import pandas as pd
import asyncio
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

if __name__ == "__main__":
    # -------------------Gather camera specific data-------------------
    loop = asyncio.get_event_loop()
    target_devices, target_networks, src_quality_profiles, src_wireless_profiles, src_camera_alerts, net_attributes \
        = loop.run_until_complete(read_functions.main(aiomeraki))


    for key in net_attributes.keys():
        print("Working on network",key,":")

        # -------------------Copy Wireless Profiles-------------------

        # Construct a set of the names in the template Wireless Profiles, and another of the names in the network
        # Wireless Profiles. Compare both sets, and determine which profiles must be created and which must be updated
        template_wp_set = set(wp['name'] for wp in src_wireless_profiles)
        net_wp_set = set(wp['name'] for wp in net_attributes[key]['wireless_profiles'])
        to_create = template_wp_set.difference(net_wp_set)
        to_update = template_wp_set.difference(to_create)

        # Construct list of wireless profiles to be created and updated based on the result of the previous set
        # operation
        create_wireless_profiles = [wp for wp in src_wireless_profiles if wp['name'] in to_create]
        update_wireless_profiles = [wp for wp in src_wireless_profiles if wp['name'] in to_update]
        for wp in update_wireless_profiles:
            for wpn in net_attributes[key]['wireless_profiles']:
                if wp['name']==wpn['name']:
                    wp['id']=wpn['id']

        print("Wireless Profiles to be Created:")
        print(tabulate(pd.DataFrame(create_wireless_profiles), headers='keys', tablefmt='fancy_grid'))
        print("Wireless Profiles to be Updated:")
        print(tabulate(pd.DataFrame(update_wireless_profiles), headers='keys', tablefmt='fancy_grid'))

        write_functions.cam_wireless_profiles(
            dashboard=dashboard,
            dst_net_id=key,
            create_wp=create_wireless_profiles,
            update_wp=update_wireless_profiles
        )

        print(f"Wireless Profiles copied to network {key} successfully.")

        # -------------------Copy Quality Profiles-------------------

        # Construct a set of the names in the template Quality Profiles, and another of the names in the network
        # Quality Profiles. Compare both sets, and determine which profiles must be created and which must be updated
        template_qp_set = set(qp['name'] for qp in src_quality_profiles)
        net_qp_set = set(qp['name'] for qp in net_attributes[key]['quality_profiles'])
        to_create = template_qp_set.difference(net_qp_set)
        to_update = template_qp_set.difference(to_create)

        # Construct list of quality profiles to be created and updated based on the result of the previous set
        # operation
        create_quality_profiles = [qp for qp in src_quality_profiles if qp['name'] in to_create]
        update_quality_profiles = [qp for qp in src_quality_profiles if qp['name'] in to_update]
        for qp in update_quality_profiles:
            for qpn in net_attributes[key]['quality_profiles']:
                if qp['name']==qpn['name']:
                    qp['id']=qpn['id']

        print("Quality Profiles to be Created:")
        print(tabulate(pd.DataFrame(create_quality_profiles), headers='keys', tablefmt='fancy_grid'))
        print("Quality Profiles to be Updated:")
        print(tabulate(pd.DataFrame(update_quality_profiles), headers='keys', tablefmt='fancy_grid'))

        write_functions.cam_quality_profiles(
            dashboard=dashboard,
            dst_net_id=key,
            create_qp=create_quality_profiles,
            update_qp=update_quality_profiles
        )

        print(f"Quality Profiles copied to network {key} successfully.")

        # -------------------Prepare QPs to assign to cameras-------------------
        # From the list of target device, find those with tags starting with qp-
        # Check that no device has more than 1 qp- tag
        qp_target_devices = []
        for dev in target_devices:
            if dev['networkId']==key:
                qp_tags = []
                for tag in dev['tags']:
                    if 'qp-' in tag:
                        qp_tags.append(tag)
                if len(qp_tags)>0 and len(qp_tags)<2:
                    qp_target_devices.append(dev)
                elif len(qp_tags)>1:
                    print(f"Error - A given camera may only have a single qp- tag for quality profiles. Skipping camera {dev['serial']}")

        # For every qp- tag, find a matching profile and assign it to the camera
        net_qps = dashboard.camera.getNetworkCameraQualityRetentionProfiles(key)
        qp_device_list = []
        for dev in qp_target_devices:
            for tag in dev['tags']:
                for qp in net_qps:
                    if tag in qp['name']:
                        device = {"name": dev['name'], "serial": dev['serial'], "quality_profile_name": qp['name'], "quality_profile_id": qp['id']}
                        qp_device_list.append(device)

        write_functions.cam_qp_assigner(dashboard=dashboard, qp_device_list=qp_device_list)

        # -------------------Prepare WPs to assign to cameras-------------------
        # For every target device, find those tagged with wp-x-y-z
        # Check that no device has more than 1 wp- tag
        wp_target_devices = []
        for dev in target_devices:
            if dev['networkId']==key:
                wp_tags = []
                for tag in dev['tags']:
                    if 'wp-' in tag:
                        wp_tags.append(tag)
                if len(wp_tags)>0 and len(wp_tags)<2:
                    wp_target_devices.append(dev)
                elif len(wp_tags)>1:
                    print(f"Error - A given camera may only have a single wp- tag for wireless profiles. Skipping camera {dev['serial']}")

        # For every wp- tag, check that it doesn't reference more than 3 wireless profiles, and that it references
        # at least 2. Then, construct a dict of IDs by finding matches in the WPs of the network
        net_wps = dashboard.camera.getNetworkCameraWirelessProfiles(key)
        wp_device_list = []
        for dev in wp_target_devices:
            for tag in dev['tags']:
                if 'wp-' in tag:
                    wp_tag = tag.split("-")
                    are_digits = all(ele.isdigit() for ele in wp_tag[1:])
                    if len(wp_tag)>=3 and len(wp_tag)<=4 and are_digits==True:
                        wps = []
                        for wp in wp_tag[1:]:
                            for prof in net_wps:
                                if f"-{wp}-" in prof['name']:
                                    wps.append(prof['id'])
                        if len(wps)==2:
                            ids = {"primary": wps[0], "secondary": wps[1]}
                        elif len(wps)==3:
                            ids = {"primary": wps[0], "secondary": wps[1], "backup": wps[2]}
                        device = {"name": dev['name'], "serial": dev['serial'], "wireless_profiles": ids}
                        wp_device_list.append(device)
                    elif len(wp_tag)<3 and are_digits==True:
                        print(f"Error - A given camera must have at least 2 different wireless profiles assigned. Camera {dev['serial']} only has {len(wp_tag)-1} WPs assigned.")
                    elif len(wp_tag)>4 and are_digits==True:
                        print(f"Error - A given camera may only have 3 different wireless profiles assigned. Skipping camera {dev['serial']}")
                    elif are_digits==False:
                        print(f"Error - The WP tag in a camera should contain dash (-) separated digits after wp only, like wp-2-1-3, where the digits reference the order of WPs to be assigned. Camera {dev['serial']} has the tag {tag} assigned.")

        write_functions.cam_wp_assigner(dashboard=dashboard, wp_device_list=wp_device_list)

        # -------------------Prepare RTSP Settings to assign to cameras-------------------
        # From the target devices, find those tagged with "rtsp" and enable RTSP on those
        rtsp_device_list = []
        for dev in target_devices:
            if dev['networkId'] == key:
                if 'rtsp' in dev['tags']:
                    device = {"name": dev['name'], "serial": dev['serial'], "rtsp_url": f"rtsp://{dev['lanIp']}:9000/live"}
                    rtsp_device_list.append(device)

        write_functions.cam_rtsp_enabler(dashboard=dashboard, rtsp_device_list=rtsp_device_list)
