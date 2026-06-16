import os
import re
from urllib.parse import urlsplit, urlunsplit

from serpapi import GoogleSearch


def normalize_linkedin_url(url):
    """Keep a clean profile URL so duplicates are easier to remove."""
    parts = urlsplit(url)
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, "", ""))


def search_google(query, limit=10):
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "SERPAPI_API_KEY is missing. Add it to your .env file or set it in PowerShell."
        )

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": limit,
    }

    results = GoogleSearch(params).get_dict()
    return results.get("organic_results", [])


def split_linkedin_title(title):
    title = re.sub(r"\s*\|\s*LinkedIn.*$", "", title or "", flags=re.IGNORECASE).strip()
    parts = [part.strip() for part in title.split(" - ") if part.strip()]

    name = parts[0] if parts else ""
    role = parts[1] if len(parts) >= 2 else ""
    company = parts[2] if len(parts) >= 3 else ""
    return name, role, company


def get_linkedin_profiles(query, limit=10):
    profiles = search_google(f"site:linkedin.com/in/ {query}", limit=limit)

    contacts = []
    seen = set()
    for profile in profiles:
        link = profile.get("link", "")
        if "linkedin.com/in/" not in link:
            continue

        clean_link = normalize_linkedin_url(link)
        if clean_link not in seen:
            seen.add(clean_link)
            name, role, company = split_linkedin_title(profile.get("title", ""))
            contacts.append(
                {
                    "linkedin_url": clean_link,
                    "name": name,
                    "role": role,
                    "company": company,
                    "title": profile.get("title", ""),
                    "snippet": profile.get("snippet", ""),
                    "source": "SerpAPI LinkedIn search result",
                }
            )

    return contacts
