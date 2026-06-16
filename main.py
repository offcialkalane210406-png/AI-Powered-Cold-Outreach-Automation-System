import argparse
import json
from pathlib import Path

from config import load_env_file

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_QUEUE_PATH = BASE_DIR / "queue.json"
DEFAULT_REJECTED_PATH = BASE_DIR / "rejected_contacts.json"


def build_queue(query, limit, queue_path, rejected_path, min_confidence):
    from generator import generate_email
    from hunter import find_email
    from search import get_linkedin_profiles
    from sources import enrich_contact_from_public_sources

    contacts = get_linkedin_profiles(query, limit=limit)
    print(f"\nFound {len(contacts)} LinkedIn search result contact(s).\n")

    queue = []
    rejected = []

    for index, contact in enumerate(contacts, start=1):
        print(f"[{index}/{len(contacts)}] Processing: {contact.get('linkedin_url')}")
        enriched = enrich_contact_from_public_sources(contact)
        discovery = find_email(enriched, min_score=min_confidence)

        if not discovery or not discovery.get("verified"):
            enriched["email_discovery"] = discovery or {
                "verified": False,
                "reason": "Missing name/company/domain for Hunter lookup.",
            }
            enriched["status"] = "rejected"
            rejected.append(enriched)
            print("Skipped: no verified email found.")
            continue

        email = generate_email(enriched)
        receiver_email = discovery["email"]
        print(
            "Queued verified email: "
            f"{receiver_email} ({discovery['confidence_score']}%, {discovery['source']})"
        )

        queue.append(
            {
                "receiver_email": receiver_email,
                "email_verified": True,
                "email_confidence_score": discovery["confidence_score"],
                "email_verification_status": discovery["verification_status"],
                "email_source": discovery["source"],
                "hunter_sources": discovery.get("hunter_sources", []),
                "profile": enriched.get("linkedin_url", ""),
                "contact": {
                    "name": enriched.get("name", ""),
                    "company": enriched.get("company", ""),
                    "role": enriched.get("role", ""),
                    "domain": enriched.get("domain", ""),
                },
                "public_sources": enriched.get("public_sources", []),
                "subject": email["subject"],
                "body": email["body"],
                "status": "pending",
            }
        )

    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(queue, indent=4), encoding="utf-8")

    rejected_path.parent.mkdir(parents=True, exist_ok=True)
    rejected_path.write_text(json.dumps(rejected, indent=4), encoding="utf-8")

    print(f"\nSaved {len(queue)} verified contact(s) to {queue_path}")
    print(f"Saved {len(rejected)} rejected/unverified contact(s) to {rejected_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Find LinkedIn URLs, discover verified emails with Hunter, and draft outreach emails."
    )
    parser.add_argument("query", nargs="?", help="Search query, for example: 'software engineer Mastercard Pune'")
    parser.add_argument("--limit", type=int, default=10, help="Maximum search results to process. Default: 10")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE_PATH, help="Path to save queue JSON.")
    parser.add_argument(
        "--rejected",
        type=Path,
        default=DEFAULT_REJECTED_PATH,
        help="Path to save contacts without verified emails.",
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=80,
        help="Minimum Hunter confidence score required for queueing. Default: 80",
    )
    return parser.parse_args()


def main():
    load_env_file(BASE_DIR / ".env")
    args = parse_args()
    query = args.query or input("Enter search query: ").strip()
    if not query:
        raise SystemExit("Search query cannot be empty.")
    build_queue(
        query=query,
        limit=args.limit,
        queue_path=args.queue,
        rejected_path=args.rejected,
        min_confidence=args.min_confidence,
    )


if __name__ == "__main__":
    main()
