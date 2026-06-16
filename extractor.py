import json
import random
import re
import time

import requests
from bs4 import BeautifulSoup


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]

BLOCK_WORDS = [
    "authwall",
    "sign in",
    "login",
    "captcha",
    "challenge",
    "unusual traffic",
    "security check",
    "access denied",
    "blocked",
]


def clean_text(value):
    """Remove extra spaces and LinkedIn separator characters."""
    if not value:
        return ""

    value = value.replace("\u00b7", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -|,\n\t")


def get_meta_content(soup, *keys):
    for key in keys:
        tag = soup.find("meta", attrs={"property": key})
        if not tag:
            tag = soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return clean_text(tag["content"])
    return ""


def is_blocked_page(response, soup):
    if response.status_code in (401, 403, 429, 999):
        return True

    page_text = soup.get_text(" ", strip=True).lower()
    page_title = clean_text(soup.title.string if soup.title else "").lower()
    check_text = f"{page_title} {page_text[:1000]}"

    return any(word in check_text for word in BLOCK_WORDS)


def fetch_page(url, retries=3, timeout=12):
    last_error = ""

    for attempt in range(1, retries + 1):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }

        try:
            response = requests.get(url, headers=headers, timeout=timeout)

            if response.status_code == 200 and response.text:
                return response, ""

            last_error = f"HTTP {response.status_code}"

        except requests.RequestException as error:
            last_error = str(error)

        if attempt < retries:
            wait_time = random.uniform(1.5, 3.5)
            time.sleep(wait_time)

    return None, last_error


def parse_json_ld(soup):
    data = {
        "name": "",
        "company": "",
        "role": "",
        "about": "",
    }

    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

    for script in scripts:
        try:
            raw = script.string or script.get_text()
            parsed = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue

        items = parsed if isinstance(parsed, list) else [parsed]

        for item in items:
            if not isinstance(item, dict):
                continue

            data["name"] = data["name"] or clean_text(item.get("name", ""))
            data["role"] = data["role"] or clean_text(item.get("jobTitle", ""))
            data["about"] = data["about"] or clean_text(item.get("description", ""))

            works_for = item.get("worksFor")
            if isinstance(works_for, dict):
                data["company"] = data["company"] or clean_text(works_for.get("name", ""))
            elif isinstance(works_for, list):
                for company in works_for:
                    if isinstance(company, dict) and company.get("name"):
                        data["company"] = data["company"] or clean_text(company["name"])
                        break

    return data


def parse_title(title):
    data = {
        "name": "",
        "company": "",
        "role": "",
    }

    title = clean_text(title)
    title = re.sub(r"\s*\|\s*LinkedIn.*$", "", title, flags=re.IGNORECASE)

    if not title:
        return data

    # Common format: "Name - Role - Company"
    parts = [clean_text(part) for part in title.split(" - ") if clean_text(part)]

    if parts:
        data["name"] = parts[0]

    if len(parts) >= 3:
        data["role"] = parts[1]
        data["company"] = parts[2]
    elif len(parts) == 2:
        second_part = parts[1]
        if any(word in second_part.lower() for word in ["engineer", "developer", "manager", "student", "founder", "analyst"]):
            data["role"] = second_part
        else:
            data["company"] = second_part

    return data


def parse_description(description):
    data = {
        "company": "",
        "role": "",
        "about": "",
    }

    description = clean_text(description)
    if not description:
        return data

    data["about"] = description

    # LinkedIn descriptions often contain:
    # "... Experience: Company Education: College Location: City ..."
    experience_match = re.search(
        r"Experience:\s*(.*?)\s*(Education:|Location:|Connections:|$)",
        description,
        flags=re.IGNORECASE,
    )
    if experience_match:
        data["company"] = clean_text(experience_match.group(1))

    role_patterns = [
        r"^(.{10,140}?)\s+Experience:",
        r"^(.{10,140}?)\s+Location:",
    ]

    for pattern in role_patterns:
        role_match = re.search(pattern, description, flags=re.IGNORECASE)
        if role_match:
            data["role"] = clean_text(role_match.group(1))
            break

    return data


def find_about_section(soup):
    possible_labels = soup.find_all(string=re.compile(r"^\s*About\s*$", re.IGNORECASE))

    for label in possible_labels:
        section = label.find_parent(["section", "div"])
        if not section:
            continue

        text = clean_text(section.get_text(" ", strip=True))
        text = re.sub(r"^About\s*", "", text, flags=re.IGNORECASE)

        if len(text) > 30:
            return text[:500]

    return ""


def extract_profile_info(url):
    info = {
        "url": url,
        "name": "",
        "company": "",
        "role": "",
        "about": "",
        "status": "unknown",
        "error": "",
    }

    response, error = fetch_page(url)

    if not response:
        info["status"] = "failed"
        info["error"] = error
        print("Extraction Error:", error)
        return info

    soup = BeautifulSoup(response.text, "html.parser")

    if is_blocked_page(response, soup):
        info["status"] = "blocked"
        info["error"] = "LinkedIn blocked or redirected this request"
        print("Blocked page:", url)
        return info

    title = clean_text(soup.title.string if soup.title else "")
    meta_title = get_meta_content(soup, "og:title", "twitter:title")
    description = get_meta_content(soup, "description", "og:description", "twitter:description")

    print("TITLE:", title or meta_title or "No title found")

    sources = [
        parse_json_ld(soup),
        parse_title(meta_title),
        parse_title(title),
        parse_description(description),
    ]

    for source in sources:
        for key in ("name", "company", "role", "about"):
            if not info[key] and source.get(key):
                info[key] = source[key]

    if not info["about"]:
        info["about"] = find_about_section(soup)

    if info["name"] or info["company"] or info["role"] or info["about"]:
        info["status"] = "success"
    else:
        info["status"] = "empty"
        info["error"] = "Page loaded, but no useful profile data was found"

    return info
