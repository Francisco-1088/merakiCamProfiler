# Authentication Config
api_key = 'ENTER_API_KEY'
base_url = 'https://api.meraki.cn/api/v1'

# Orgs and Networks
src_org_id = 'ENTER_SOURCE_ORG_ID'
dst_org_id = 'ENTER_TARGET_ORG_ID' # can be the same as src_org_id if copying within the same org
src_net_id = 'ENTER_NETWORK_ID'

# Modules to Sync ----NOT IMPLEMENTED YET
# Keep only the modules you want to sync
# Available modules: quality_profiles, wireless_profiles, rtsp_settings
modules = ['quality_profiles', 'wireless_profiles', 'rtsp_settings']

# Tag Config
dst_network_tag = 'camProfiler'
dst_camera_tag = 'camProfiler'
rtsp_enable_tag = 'rtsp'

# Logging, Verbosity and Supervision
verbose = True # Will display information gathered about networks
supervised = True # Will ask before applying any configuration changes
console_logging = True # Will print API output to the console
max_retries = 100 # Number of times the API will retry when finding errors like 429
max_requests = 10 # Number of concurrent requests to the API