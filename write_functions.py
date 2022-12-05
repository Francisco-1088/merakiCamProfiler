import time
import config
import pandas as pd
from tabulate import tabulate

def cam_wireless_profiles(dashboard, dst_net_id, create_wp, update_wp):
    """
    Copies port schedules from source template to target network
    :param dashboard: Dashboard API client instance
    :param dst_net_id: ID of target network
    :param create_wp: Wireless Profiles to be created in target network
    :param update_wp: Wireless Profiles to be updated in target network
    :return:
    """
    if config.supervised==True:
        print("Script will create the following Wireless Profiles:")
        print(tabulate(pd.DataFrame(create_wp), headers='keys', tablefmt='fancy_grid'))
        print("Script will update the following Wireless Profiles:")
        print(tabulate(pd.DataFrame(update_wp), headers='keys', tablefmt='fancy_grid'))
        proceed = input("Do you wish to proceed? (Y/N):")
        if proceed == 'Y':
            for cwp in create_wp:
                upd = {k: cwp[k] for k in cwp.keys() - {
                    "id",
                    "networkId",
                    "name"
                }}
                dashboard.camera.createNetworkCameraWirelessProfile(
                    networkId=dst_net_id,
                    name=cwp['name'],
                    **upd,
                )
            for uwp in update_wp:
                wp_id = uwp['id']
                upd = {k: uwp[k] for k in uwp.keys() - {
                    "id",
                    "networkId",
                    "name"
                }}
                dashboard.camera.updateNetworkCameraWirelessProfile(
                    networkId=dst_net_id,
                    wirelessProfileId=wp_id,
                    **upd,
                )
        elif proceed=='N':
            print("Skipping configuration of Wireless Profiles can cause conflicts with camera configurations! Aborting Script!")
            exit()
        else:
            print("Unexpected Input!")
            exit()
    else:
        for cwp in create_wp:
            upd = {k: cwp[k] for k in cwp.keys() - {
                "id",
                "networkId",
                "name"
            }}
            dashboard.camera.createNetworkCameraWirelessProfile(
                networkId=dst_net_id,
                name=cwp['name'],
                **upd,
            )
        for uwp in update_wp:
            wp_id = uwp['id']
            upd = {k: uwp[k] for k in uwp.keys() - {
                "id",
                "networkId",
                "name"
            }}
            dashboard.camera.updateNetworkCameraWirelessProfile(
                networkId=dst_net_id,
                wirelessProfileId=wp_id,
                **upd,
            )

def cam_quality_profiles(dashboard, dst_net_id, create_qp, update_qp):
    """
    Copies port schedules from source template to target network
    :param dashboard: Dashboard API client instance
    :param dst_net_id: ID of target network
    :param create_qp: Quality Profiles to be created in target network
    :param update_qp: Quality Profiles to be updated in target network
    :return:
    """
    if config.supervised==True:
        print("Script will create the following Wireless Profiles:")
        print(tabulate(pd.DataFrame(create_qp), headers='keys', tablefmt='fancy_grid'))
        print("Script will update the following Wireless Profiles:")
        print(tabulate(pd.DataFrame(update_qp), headers='keys', tablefmt='fancy_grid'))
        proceed = input("Do you wish to proceed? (Y/N):")
        if proceed == 'Y':
            for cqp in create_qp:
                upd = {k: cqp[k] for k in cqp.keys() - {
                    "id",
                    "networkId",
                    "name"
                }}
                dashboard.camera.createNetworkCameraQualityRetentionProfile(
                    networkId=dst_net_id,
                    name=cqp['name'],
                    **upd,
                )
            for uqp in update_qp:
                qp_id = uqp['id']
                upd = {k: uqp[k] for k in uqp.keys() - {
                    "id",
                    "networkId",
                    "name"
                }}
                dashboard.camera.updateNetworkCameraQualityRetentionProfile(
                    networkId=dst_net_id,
                    qualityRetentionProfileId=qp_id,
                    **upd,
                )
        elif proceed=='N':
            print("Skipping configuration of Wireless Profiles can cause conflicts with camera configurations! Aborting Script!")
            exit()
        else:
            print("Unexpected Input!")
            exit()
    else:
        for cqp in create_qp:
            upd = {k: cqp[k] for k in cqp.keys() - {
                "id",
                "networkId",
                "name"
            }}
            dashboard.camera.createNetworkCameraQualityRetentionProfile(
                networkId=dst_net_id,
                name=cqp['name'],
                **upd,
            )
        for uqp in update_qp:
            qp_id = uqp['id']
            upd = {k: uqp[k] for k in uqp.keys() - {
                "id",
                "networkId",
                "name"
            }}
            dashboard.camera.updateNetworkCameraQualityRetentionProfile(
                networkId=dst_net_id,
                qualityRetentionProfileId=qp_id,
                **upd,
            )

def cam_qp_assigner(dashboard, qp_device_list):
    """
    Assigns Quality Profiles to Cameras
    :param dashboard: Dashboard API client instance
    :param qp_device_list: List of cameras to be assigned quality profiles in the network
    :return:
    """
    if config.supervised==True:
        print("Script will assign Quality Profiles to the following Cameras:")
        print(tabulate(pd.DataFrame(qp_device_list), headers='keys', tablefmt='fancy_grid'))
        proceed = input("Do you wish to proceed? (Y/N):")
        if proceed == 'Y':
            for camera in qp_device_list:
                dashboard.camera.updateDeviceCameraQualityAndRetention(
                    serial=camera['serial'],
                    profileId=camera['quality_profile_id']
                )
        elif proceed=='N':
            print("Skipping assignment of Quality Profiles for these cameras.")
        else:
            print("Unexpected Input! Skipping assignment of Quality Profiles for these cameras!")
    else:
        if config.verbose==True:
            print("Script will assign Quality Profiles to the following Cameras:")
            print(tabulate(pd.DataFrame(qp_device_list), headers='keys', tablefmt='fancy_grid'))
        for camera in qp_device_list:
            dashboard.camera.updateDeviceCameraQualityAndRetention(
                serial=camera['serial'],
                profileId=camera['quality_profile_id']
            )

def cam_wp_assigner(dashboard, wp_device_list):
    """
    Assigns Wireless Profiles to Cameras
    :param dashboard: Dashboard API client instance
    :param wp_device_list: List of cameras to be assigned wireless profiles in the network
    :return:
    """
    if config.supervised==True:
        print("Script will assign Quality Profiles to the following Cameras:")
        print(tabulate(pd.DataFrame(wp_device_list), headers='keys', tablefmt='fancy_grid'))
        proceed = input("Do you wish to proceed? (Y/N):")
        if proceed == 'Y':
            for camera in wp_device_list:
                dashboard.camera.updateDeviceCameraWirelessProfiles(
                    serial=camera['serial'],
                    ids=camera['wireless_profiles']
                )
        elif proceed=='N':
            print("Skipping assignment of Wireless Profiles for these cameras.")
        else:
            print("Unexpected Input! Skipping assignment of Wireless Profiles for these cameras!")
    else:
        if config.verbose==True:
            print("Script will assign Wireless Profiles to the following Cameras:")
            print(tabulate(pd.DataFrame(wp_device_list), headers='keys', tablefmt='fancy_grid'))
        for camera in wp_device_list:
            dashboard.camera.updateDeviceCameraWirelessProfiles(
                serial=camera['serial'],
                ids=camera['wireless_profiles']
            )

def cam_rtsp_enabler(dashboard, rtsp_device_list):
    """
    Activates RTSP in cameras
    :param dashboard: Dashboard API client instance
    :param wp_device_list: List of cameras to RTSP turned on
    :return:
    """
    if config.supervised==True:
        print("Script will activate RTSP in the following Cameras:")
        print(tabulate(pd.DataFrame(rtsp_device_list), headers='keys', tablefmt='fancy_grid'))
        proceed = input("Do you wish to proceed? (Y/N):")
        if proceed == 'Y':
            for camera in rtsp_device_list:
                dashboard.camera.updateDeviceCameraVideoSettings(
                    serial=camera['serial'],
                    externalRstpEnabled=True
                )
        elif proceed=='N':
            print("Skipping activation of RTSP for these cameras.")
        else:
            print("Unexpected Input! Skipping activation of RTSP for these cameras!")
    else:
        if config.verbose==True:
            print("Script will activate RTSP in the following Cameras:")
            print(tabulate(pd.DataFrame(rtsp_device_list), headers='keys', tablefmt='fancy_grid'))
        for camera in rtsp_device_list:
            dashboard.camera.updateDeviceCameraVideoSettings(
                serial=camera['serial'],
                externalRstpEnabled=True
            )

def cam_batcher(dashboard, dst_org_id, actions):
    """
    Copies port schedules from source template to target network
    :param dashboard: Dashboard API client instance
    :param dst_org_id: ID of target organization
    :param actions: list of actions to create the action batch
    :return:
    """
    for i in range(0, len(actions), 100):
        if i>=4:
            time.sleep(2)
        # Check for unfinished batches
        j = False
        while not j:
            print("Checking for unfinished batches...")
            pending_batches = dashboard.organizations.getOrganizationActionBatches(dst_org_id, status='pending')
            print("Current pending batches:",pending_batches)
            if len(pending_batches) > 4:
                j = False
                print(f"You have {len(pending_batches)} unfinished batches:")
                for item in pending_batches:
                    print(item['id'])
                print("Waiting to complete some of these before scheduling a new one!")
                time.sleep(10)
            elif len(pending_batches) <= 4:
                j = True
        subactions = actions[i:i + 100]
        print("Creating Camera Settings Action Batch...")
        dashboard.organizations.createOrganizationActionBatch(
            organizationId=dst_org_id,
            actions=subactions,
            confirmed=True,
            synchronous=False
        )
        time.sleep(1)
