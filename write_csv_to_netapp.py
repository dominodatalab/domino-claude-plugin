import csv
import os
import random
import string
from datetime import datetime, timedelta

# Volume mount path (git-based project)
VOLUME_PATH = "/mnt/netapp-volumes/claude_test"

# Generate random customer data
random.seed(42)

def random_name():
    first = random.choice(["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank"])
    last = random.choice(["Smith", "Jones", "Williams", "Brown", "Davis", "Miller", "Wilson"])
    return first, last

rows = []
base_date = datetime(2024, 1, 1)
for i in range(1, 101):
    first, last = random_name()
    rows.append({
        "id": i,
        "first_name": first,
        "last_name": last,
        "email": f"{first.lower()}.{last.lower()}{i}@example.com",
        "age": random.randint(22, 65),
        "score": round(random.uniform(0, 100), 2),
        "signup_date": (base_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
        "active": random.choice([True, False]),
    })

output_path = os.path.join(VOLUME_PATH, "customers.csv")
with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Written {len(rows)} rows to {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")
print("First 3 rows:")
for row in rows[:3]:
    print(" ", row)
