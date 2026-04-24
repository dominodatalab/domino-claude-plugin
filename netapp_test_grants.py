"""
Steps 2 & 3: Add agnes_domino as VolumeReader, attach volume to project.
"""
import os
import requests
import json

token = requests.get("http://localhost:8899/access-token").text.strip()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
api_url = os.environ["DOMINO_API_HOST"]
remotefs_url = os.environ["DOMINO_REMOTE_FILE_SYSTEM_HOSTPORT"]
project_id = os.environ["DOMINO_PROJECT_ID"]

VOLUME_ID = "335b191b-9dd0-467c-8c67-4eec18cfea01"
MY_USER_ID = "690a96caa4464d12be7f6e83"
AGNES_USER_ID = "69160c9da4464d12be7f6e84"

# --- 2. Add agnes_domino as VolumeReader ---
# The create response showed grants is a list; PUT replaces all grants
updated_grants = [
    {"targetId": MY_USER_ID, "targetRole": "VolumeOwner"},
    {"targetId": AGNES_USER_ID, "targetRole": "VolumeReader"},
]
grant_resp = requests.put(
    f"{remotefs_url}/remotefs/v1/volumes/{VOLUME_ID}/grants",
    headers=headers,
    json=updated_grants,
)
print(f"Update grants status: {grant_resp.status_code}")
print(json.dumps(grant_resp.json(), indent=2))

# --- 3. Attach volume to current project ---
attach_resp = requests.post(
    f"{remotefs_url}/remotefs/v1/rpc/attach-volume-to-project",
    headers=headers,
    json={"volumeId": VOLUME_ID, "projectId": project_id},
)
print(f"\nAttach to project status: {attach_resp.status_code}")
print(attach_resp.text)

print("\n=== Steps 2 & 3 complete ===")
print(f"Volume ID: {VOLUME_ID}")
