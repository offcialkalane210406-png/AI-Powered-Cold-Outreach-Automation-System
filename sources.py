import re
from urllib.parse import urlsplit

from search import search_google


BLOCKED_DOMAINS = {
    "linkedin.com",
    "www.linkedin.com",
    "facebook.com",
    "www.facebook.com",
    "instagram.com",
    "www.instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "www.youtube.com",
    "google.com",
    "www.google.com",
}


def clean_company(value):
    value = re.sub(r"\b(currently|working|at|in)\b", "", value or "", flags=re.IGNORECASE)
    value = re.sub(r"[^a-zA-Z0-9&., ]", " ", value)
    return re.sub(r"\s+", " ", value).strip(" .,")


def extract_company_from_text(text):
    text = text or ""
    patterns = [
        r"\bat\s+([A-Z][A-Za-z0-9&., ]{2,60})",
        r"\bworks\s+at\s+([A-Z][A-Za-z0-9&., ]{2,60})",
        r"\bfrom\s+([A-Z][A-Za-z0-9&., ]{2,60})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return clean_company(match.group(1))
    return ""


def domain_from_url(url):
    netloc = urlsplit(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def is_company_domain(domain):
    if not domain or domain in BLOCKED_DOMAINS:
        return False
    return not any(domain.endswith("." + blocked) for blocked in BLOCKED_DOMAINS)


def enrich_contact_from_public_sources(contact, limit=5):
    name = contact.get("name", "")
    company = clean_company(contact.get("company", ""))
    snippet = contact.get("snippet", "")

    if not company:
        company = extract_company_from_text(snippet)

    query_parts = [part for part in [name, company, "company website"] if part]
    query = " ".join(f'"{part}"' if " " in part else part for part in query_parts)
    results = search_google(query, limit=limit) if query_parts else []

    sources = []
    candidate_domain = ""

    for result in results:
        link = result.get("link", "")
        domain = domain_from_url(link)
        if not is_company_domain(domain):
            continue

        source = {
            "title": result.get("title", ""),
            "link": link,
            "snippet": result.get("snippet", ""),
            "domain": domain,
            "source": "SerpAPI public web search",
        }
        sources.append(source)

        if not candidate_domain:
            candidate_domain = domain

        if not company:
            company = extract_company_from_text(result.get("title", "") + " " + result.get("snippet", ""))

    return {
        **contact,
        "company": company,
        "domain": candidate_domain,
        "public_sources": sources,
    }
