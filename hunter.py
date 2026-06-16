import os

import requests

HUNTER_BASE_URL = "https://api.hunter.io/v2"
VERIFIED_STATUSES = {"valid"}


def split_name(full_name):
    parts = [part for part in (full_name or "").strip().split() if part]
    if len(parts) < 2:
        return "", ""
    return parts[0], parts[-1]


def hunter_get(endpoint, params, timeout=20):
    api_key = os.getenv("HUNTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("HUNTER_API_KEY is missing. Add it to your .env file.")

    request_params = {**params, "api_key": api_key}
    response = requests.get(f"{HUNTER_BASE_URL}/{endpoint}", params=request_params, timeout=timeout)
    response.raise_for_status()
    return response.json().get("data", {})


def verification_status(data):
    verification = data.get("verification") or {}
    return (
        verification.get("status")
        or verification.get("result")
        or data.get("status")
        or data.get("result")
        or ""
    ).lower()


def verify_email(email):
    if not email:
        return {"status": "", "score": 0}

    data = hunter_get("email-verifier", {"email": email})
    return {
        "status": verification_status(data),
        "score": data.get("score") or data.get("confidence") or 0,
        "raw": data,
    }


def find_email(contact, min_score=80):
    first_name, last_name = split_name(contact.get("name", ""))
    if not first_name or not last_name:
        return None

    params = {
        "first_name": first_name,
        "last_name": last_name,
    }
    if contact.get("domain"):
        params["domain"] = contact["domain"]
    elif contact.get("company"):
        params["company"] = contact["company"]
    else:
        return None

    data = hunter_get("email-finder", params)
    email = data.get("email", "")
    score = data.get("score") or data.get("confidence") or 0
    status = verification_status(data)

    if email and status not in VERIFIED_STATUSES:
        verifier = verify_email(email)
        status = verifier["status"]
        score = max(score, verifier["score"] or 0)
        data["verification_check"] = verifier["raw"]

    if not email or score < min_score or status not in VERIFIED_STATUSES:
        return {
            "email": email,
            "verified": False,
            "confidence_score": score,
            "verification_status": status,
            "source": "Hunter",
            "raw": data,
        }

    return {
        "email": email,
        "verified": True,
        "confidence_score": score,
        "verification_status": status,
        "source": "Hunter",
        "hunter_sources": data.get("sources", []),
        "raw": data,
    }
