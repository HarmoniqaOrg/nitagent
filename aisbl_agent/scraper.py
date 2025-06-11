import os
import re
import csv
import logging
from dataclasses import dataclass, asdict
from typing import Iterable, List, Optional

import openai
import requests
from bs4 import BeautifulSoup


EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}")


@dataclass
class ContactInfo:
    organization_name: str
    website: Optional[str] = None
    emails: List[str] = None
    phones: List[str] = None
    personnel: Optional[str] = None


def search_website(query: str) -> Optional[str]:
    """Search DuckDuckGo and return the first result URL."""
    logging.debug("Searching for %s", query)
    params = {"q": query, "t": "h_", "ia": "web"}
    resp = requests.get("https://duckduckgo.com/html/", params=params, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    result = soup.find("a", {"class": "result__a"})
    if not result:
        return None
    href = result.get("href")
    if (href.startswith("/l/?") or href.startswith("//duckduckgo.com/l/")) and "uddg=" in href:
        from urllib.parse import parse_qs, urlparse, unquote

        qs = parse_qs(urlparse(href).query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    if href.startswith("//"):
        return "https:" + href
    return href


def fetch_page(url: str) -> str:
    logging.debug("Fetching page %s", url)
    resp = requests.get(url, timeout=10)
    return resp.text


def extract_contacts(text: str) -> (List[str], List[str]):
    emails = list(set(EMAIL_RE.findall(text)))
    phones = list(set(PHONE_RE.findall(text)))
    return emails, phones


def extract_personnel(text: str) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    openai.api_key = api_key
    prompt = (
        "Extract names, titles, and contact details of key personnel from the "
        "following text. Respond with a short summary:\n" + text[:4000]
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logging.error("OpenAI extraction failed: %s", exc)
        return None


def process_organization(name: str) -> ContactInfo:
    website = search_website(name)
    emails, phones, personnel = [], [], None
    if website:
        html = fetch_page(website)
        emails, phones = extract_contacts(html)
        personnel = extract_personnel(html)
    return ContactInfo(
        organization_name=name,
        website=website,
        emails=emails,
        phones=phones,
        personnel=personnel,
    )


def process_rows(rows: Iterable[dict]) -> List[ContactInfo]:
    """Process an iterable of CSV rows and return contact info objects."""
    results: List[ContactInfo] = []
    for row in rows:
        name = row.get("organization_name")
        if not name:
            continue
        logging.info("Processing %s", name)
        info = process_organization(name)
        results.append(info)
    return results


def process_csv(input_csv: str, output_csv: str) -> None:
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        results = process_rows(reader)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "organization_name",
            "website",
            "emails",
            "phones",
            "personnel",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for info in results:
            row = asdict(info)
            row["emails"] = ";".join(info.emails or [])
            row["phones"] = ";".join(info.phones or [])
            writer.writerow(row)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape AISBL contact data")
    parser.add_argument("input_csv", help="CSV file with organization_name column")
    parser.add_argument("output_csv", help="Destination CSV for results")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    process_csv(args.input_csv, args.output_csv)
