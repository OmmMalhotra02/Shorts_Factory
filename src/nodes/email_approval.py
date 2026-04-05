import yagmail
import imaplib
import email
import time
import uuid
from datetime import datetime, timezone
from typing import Dict
from state import ShortsState
import os
from dotenv import load_dotenv
load_dotenv()
import json

SENDER_EMAIL = os.getenv('SENDER_EMAIL')
APP_PASSWORD = os.getenv('GMAIL_PASSWORD')

# -------------------------
# Send Email
# -------------------------

def send_email(state: ShortsState):
    yag = yagmail.SMTP(
        user=SENDER_EMAIL,
        password=APP_PASSWORD,
        host="smtp.gmail.com",
        port=587,
        smtp_starttls=True,
        smtp_ssl=False
    )

    request_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc)

    subject = f"[SHORTS APPROVAL][{request_id}] {state['topic']}"

    body = f"""
        Request ID: {request_id}

        Topic: {state['topic']}

        Script:
        {state['script']}

        Caption:
        {state['caption']}

        Reply with ONE of the following:

        approve

        script change: <your feedback>

        media change: <your feedback>

        both: <your feedback>
    """

    os.makedirs("approvals", exist_ok=True)
    # 🔥 SAVE REQUEST
    data = {
        "request_id": request_id,
        "sent_time": timestamp.isoformat(),
        "state": state,
        "status": "pending"
    }

    def serialize(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    os.makedirs("approvals", exist_ok=True)

    data = {
        "request_id": request_id,
        "sent_time": timestamp.isoformat(),
        "state": state,
        "status": "pending"
    }

    with open(f"approvals/{request_id}.json", "w") as f:
        json.dump(data, f, default=serialize, indent=2)

    if not os.path.exists(state["video_path"]):
        raise FileNotFoundError(f"🚨 Video not found: {state['video_path']}")

    yag.send(
        to=SENDER_EMAIL,
        subject=subject,
        contents=body,
        attachments=[state["video_path"]]
    )

    return request_id, timestamp


# -------------------------
# Clean Email Body
# -------------------------
def clean_body(body: str) -> str:
    """
    Remove quoted replies and signatures
    """
    lines = body.splitlines()
    clean_lines = []

    for line in lines:
        # stop at quoted text
        if line.strip().startswith(">"):
            break
        if "On" in line and "wrote:" in line:
            break
        clean_lines.append(line)

    return "\n".join(clean_lines).strip().lower()


# -------------------------
# Read Email Reply
# -------------------------
def check_reply(request_id: str, sent_time: datetime, timeout=3600, interval=15):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(SENDER_EMAIL, APP_PASSWORD)

    start_time = time.time()

    while time.time() - start_time < timeout:
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()

        for mail_id in reversed(mail_ids[-15:]):  # recent emails only
            status, msg_data = mail.fetch(mail_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = msg["subject"] or ""

            # match request id
            if request_id not in subject:
                continue

            # check timestamp (avoid old matches)
            email_date = msg["date"]
            email_dt = email.utils.parsedate_to_datetime(email_date)

            email_dt = email.utils.parsedate_to_datetime(email_date)

            if email_dt.tzinfo is None:
                email_dt = email_dt.replace(tzinfo=timezone.utc)

            if email_dt < sent_time:
                continue

            # extract body
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        return clean_body(body)
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")
                return clean_body(body)

        time.sleep(interval)

    return None  # timeout


# -------------------------
# Parse Reply
# -------------------------
def parse_review(reply: str):
    if reply is None:
        return "none", ""

    reply = reply.strip()

    if reply.startswith("approve"):
        return "none", ""

    elif reply.startswith("script change"):
        return "script", reply.replace("script change:", "").strip()

    elif reply.startswith("media change"):
        return "media", reply.replace("media change:", "").strip()

    elif reply.startswith("both"):
        return "both", reply.replace("both:", "").strip()

    return "none", ""


# -------------------------
# Main Node
# -------------------------
def email_approval(state: ShortsState) -> dict:
    request_id, sent_time = send_email(state)
    
    # save pending approval file
    approval_file = f"approvals/{request_id}.json"
    
    # just watch the file — approval_worker handles IMAP
    while True:
        with open(approval_file) as f:
            data = json.load(f)
        if data["status"] == "done":
            return {
                "is_reviewed": True,
                "review": data["review"],
                "review_type": data["review_type"]
            }
        
        if data["status"] == "timeout":      # ← add this block
            print("⏰ Approval timed out")
            return {
                "is_reviewed": False,
                "review": "",
                "review_type": "none"
            }

        time.sleep(10)