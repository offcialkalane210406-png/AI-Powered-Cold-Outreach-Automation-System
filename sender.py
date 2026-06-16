import argparse
import json
import os
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

from config import load_env_file
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_QUEUE_PATH = BASE_DIR / "queue.json"


def get_required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is missing. Add it to your .env file.")
    return value


def send_email(sender_email, app_password, receiver_email, subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)


def load_queue(path):
    if not path.exists():
        raise FileNotFoundError(f"Queue file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_queue(path, queue):
    path.write_text(json.dumps(queue, indent=4), encoding="utf-8")


def process_queue(queue_path, dry_run=True, delay_seconds=3):
    load_env_file(BASE_DIR / ".env")
    queue = load_queue(queue_path)

    sender_email = ""
    app_password = ""
    if not dry_run:
        sender_email = get_required_env("GMAIL_ADDRESS")
        app_password = get_required_env("GMAIL_APP_PASSWORD")

    sent_count = 0
    skipped_count = 0

    for item in queue:
        if item.get("status") != "pending":
            skipped_count += 1
            continue

        receiver = item.get("receiver_email", "").strip()
        is_verified = item.get("email_verified") is True
        if not receiver or not is_verified:
            item["status"] = "needs_review"
            item["error"] = "Missing receiver_email or email_verified is not true."
            skipped_count += 1
            continue

        subject = item.get("subject") or "Seeking career guidance"
        body = item.get("body") or item.get("email", "")

        if dry_run:
            print(f"DRY RUN: would send to {receiver} | Subject: {subject}")
            skipped_count += 1
            continue

        try:
            send_email(sender_email, app_password, receiver, subject, body)
            item["status"] = "sent"
            item.pop("error", None)
            sent_count += 1
            print(f"Sent email to {receiver}")
            time.sleep(delay_seconds)
        except Exception as error:
            item["status"] = "failed"
            item["error"] = str(error)
            print(f"Failed to send to {receiver}: {error}")

    save_queue(queue_path, queue)
    print(f"Done. Sent: {sent_count}. Skipped/review: {skipped_count}.")


def parse_args():
    parser = argparse.ArgumentParser(description="Send reviewed emails from queue.json.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE_PATH, help="Queue JSON path.")
    parser.add_argument("--send", action="store_true", help="Actually send emails. Without this, sender runs in dry-run mode.")
    parser.add_argument("--delay", type=int, default=3, help="Delay in seconds between emails. Default: 3")
    return parser.parse_args()


def main():
    args = parse_args()
    process_queue(args.queue, dry_run=not args.send, delay_seconds=args.delay)


if __name__ == "__main__":
    main()
