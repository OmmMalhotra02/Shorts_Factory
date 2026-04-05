import os
import sys
import json
import time
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nodes.email_approval import check_reply, parse_review

APPROVAL_DIR = "approvals"

# ensure directory exists
if not os.path.exists(APPROVAL_DIR):
    os.makedirs(APPROVAL_DIR)

while True:
    for file in os.listdir(APPROVAL_DIR):

        if not file.endswith(".json"):
            continue

        path = os.path.join(APPROVAL_DIR, file)

        # safe read
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Skipping corrupt file {file}: {e}")
            continue

        if data.get("status") != "pending":
            continue

        request_id = data["request_id"]
        sent_time = datetime.fromisoformat(data["sent_time"])

        # ensure timezone-aware
        if sent_time.tzinfo is None:
            sent_time = sent_time.replace(tzinfo=timezone.utc)

        # timeout safety
        max_wait_minutes = 30
        if (datetime.now(timezone.utc) - sent_time).total_seconds() > max_wait_minutes * 60:
            data["status"] = "timeout"
            with open(path, "w") as f:
                json.dump(data, f)
            print(f"⏰ Timeout: {request_id}")
            continue

        reply = check_reply(request_id, sent_time, timeout=5)

        if reply is not None:
            review_type, review = parse_review(reply)

            data["status"] = "done"
            data["review"] = review
            data["review_type"] = review_type

            with open(path, "w") as f:
                json.dump(data, f)

            print(f"✅ Approved: {request_id} | Type: {review_type}")

    time.sleep(10)