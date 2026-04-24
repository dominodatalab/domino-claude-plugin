"""
Job script: writes a random file to the attached NetApp volume.
Run with volume skill-test-volume mounted and snapshotNetAppVolumesOnCompletion=True.
"""
import os
import random
import string
import datetime

def detect_mount_root():
    if os.path.exists("/mnt/netapp-volumes"):
        return "/mnt/netapp-volumes"
    elif os.path.exists("/domino/netapp-volumes"):
        return "/domino/netapp-volumes"
    return None

netapp_root = detect_mount_root()
if netapp_root is None:
    raise RuntimeError("NetApp volume root not found — is the volume attached to this job?")

print(f"Project type detected: {'Git-Based' if 'mnt' in netapp_root else 'DFS'}")
print(f"NetApp root: {netapp_root}")

volume_path = f"{netapp_root}/skill-test-volume"
print(f"Volume path: {volume_path}")
print(f"Volume contents before write: {os.listdir(volume_path)}")

random_content = "".join(random.choices(string.ascii_letters + string.digits, k=256))
timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
filename = f"random_file_{timestamp}.txt"
filepath = os.path.join(volume_path, filename)

with open(filepath, "w") as f:
    f.write(f"Written by netapp_write_test.py at {timestamp}\n")
    f.write(f"Random content: {random_content}\n")

print(f"\nWrote file: {filepath}")
print(f"Volume contents after write: {os.listdir(volume_path)}")
print("Job complete.")
