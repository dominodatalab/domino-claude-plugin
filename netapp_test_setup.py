"""
NetApp Volumes skill test — steps 1, 2, 3:
  1. Create a new NetApp volume
  2. Add agnes_domino as VolumeReader
  3. Attach the volume to the current project
"""
import os
import requests
import json

# --- Auth (in-cluster) ---
token = requests.get("http://localhost:8899/access-token").text.strip()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
api_url = os.environ["DOMINO_API_HOST"]
remotefs_url = os.environ["DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT"]
project_id = os.environ["DOMINO_PROJECT_ID"]
my_username = os.environ["DOMINO_USER_NAME"]

# --- Look up my user ID ---
me = requests.get(
    f"{api_url}/v4/users?userName={my_username}", headers=headers
).json()
my_user_id = me[0]["id"]
print(f"My user ID ({my_username}): {my_user_id}")

# --- Look up agnes_domino's user ID ---
agnes_resp = requests.get(
    f"{api_url}/v4/users?userName=agnes_domino", headers=headers
).json()
print(f"\nagnes_domino lookup response: {json.dumps(agnes_resp, indent=2)}")
agnes_user_id = agnes_resp[0]["id"]
print(f"agnes_domino user ID: {agnes_user_id}")

# --- 1. Create the volume ---
FILESYSTEM_ID = "ea966c8b-e586-4df0-8584-d27f6dad4bff"
volume_resp = requests.post(
    f"{remotefs_url}/remotefs/v1/volumes",
    headers=headers,
    json={
        "name": "skill-test-volume",
        "description": "Test volume created by NetApp Volumes skill test",
        "filesystemId": FILESYSTEM_ID,
        "capacity": 10_000_000_000,  # 10 GB
        "grants": [
            {"targetId": my_user_id, "targetRole": "VolumeOwner"}
        ],
    },
)
print(f"\nCreate volume status: {volume_resp.status_code}")
volume = volume_resp.json()
print(json.dumps(volume, indent=2))
volume_id = volume["id"]
print(f"\nCreated volume ID: {volume_id}")

# --- 2. Add agnes_domino as VolumeReader ---
# First fetch existing grants so we don't overwrite them
grants_resp = requests.get(
    f"{remotefs_url}/remotefs/v1/volumes/{volume_id}/grants",
    headers=headers,
)
existing_grants = grants_resp.json().get("data", [])
updated_grants = [
    {"targetId": g["targetId"], "targetRole": g["targetRole"]}
    for g in existing_grants
]
# Add agnes if not already present
if not any(g["targetId"] == agnes_user_id for g in updated_grants):
    updated_grants.append({"targetId": agnes_user_id, "targetRole": "VolumeReader"})

grant_resp = requests.put(
    f"{remotefs_url}/remotefs/v1/volumes/{volume_id}/grants",
    headers=headers,
    json=updated_grants,
)
print(f"\nUpdate grants status: {grant_resp.status_code}")
print(json.dumps(grant_resp.json(), indent=2))

# --- 3. Attach volume to current project ---
attach_resp = requests.post(
    f"{remotefs_url}/remotefs/v1/rpc/attach-volume-to-project",
    headers=headers,
    json={"volumeId": volume_id, "projectId": project_id},
)
print(f"\nAttach to project status: {attach_resp.status_code}")
print(attach_resp.text)

print(f"\n=== SETUP COMPLETE ===")
print(f"Volume ID: {volume_id}")
print(f"Volume name: skill-test-volume")
