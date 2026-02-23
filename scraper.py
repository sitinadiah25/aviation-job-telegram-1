import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import urllib.parse

logger = logging.getLogger(__name__)

# Keywords relevant to the user's background
SEARCH_QUERIES = [
    "aviation management",
    "airport operations",
    "airline operations",
    "project manager aviation",
    "data analyst aviation",
    "air transport",
    "flight operations",
    "ground handling management",
    "aviation project management",
    "operations analyst",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ─── MyCareersFuture ─────────────────────────────────────────────────────────

async def fetch_mcf(session: aiohttp.ClientSession) -> list[dict]:
    jobs = []
    keywords = [
        "aviation", "air transport", "project manager", "data analyst",
        "airport", "airline", "operations manager"
    ]
    for keyword in keywords[:4]:  # limit requests
        try:
            url = (
                f"https://www.mycareersfuture.gov.sg/api/v2/search"
                f"?search={urllib.parse.quote(keyword)}&limit=10&page=0"
                f"&sortBy=new_posting_date"
            )
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    for item in results:
                        jobs.append({
                            "source": "MyCareersFuture",
                            "title": item.get("title", ""),
                            "company": item.get("postedCompany", {}).get("name", ""),
                            "location": "Singapore",
                            "url": f"https://www.mycareersfuture.gov.sg/job/{item.get('uuid', '')}",
                            "salary": _mcf_salary(item),
                            "snippet": item.get("minimumYearsExperience", ""),
                        })
        except Exception as e:
            logger.warning(f"MCF error for '{keyword}': {e}")
        await asyncio.sleep(1)
    return jobs


def _mcf_salary(item):
    sal_min = item.get("salary", {}).get("minimum")
    sal_max = item.get("salary", {}).get("maximum")
    if sal_min and sal_max:
        return f"SGD {sal_min:,} – {sal_max:,}/month"
    return ""


# ─── Indeed (Singapore) ──────────────────────────────────────────────────────

async def fetch_indeed(session: aiohttp.ClientSession) -> list[dict]:
    jobs = []
    queries = [
        ("aviation operations", "Singapore"),
        ("project manager aviation", "Singapore"),
        ("data analyst aviation", "Singapore"),
        ("airport operations manager", "Singapore"),
    ]
    for q, loc in queries:
        try:
            url = (
                f"https://sg.indeed.com/jobs"
                f"?q={urllib.parse.quote(q)}&l={urllib.parse.quote(loc)}&sort=date"
            )
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    cards = soup.select("div.job_seen_beacon")[:5]
                    for card in cards:
                        title_el = card.select_one("h2.jobTitle span")
                        company_el = card.select_one("[data-testid='company-name']")
                        location_el = card.select_one("[data-testid='text-location']")
                        link_el = card.select_one("h2.jobTitle a")
                        if title_el and link_el:
                            job_id = link_el.get("data-jk", "")
                            jobs.append({
                                "source": "Indeed",
                                "title": title_el.get_text(strip=True),
                                "company": company_el.get_text(strip=True) if company_el else "",
                                "location": location_el.get_text(strip=True) if location_el else "Singapore",
                                "url": f"https://sg.indeed.com/viewjob?jk={job_id}" if job_id else f"https://sg.indeed.com{link_el.get('href','')}",
                                "salary": "",
                                "snippet": "",
                            })
        except Exception as e:
            logger.warning(f"Indeed error for '{q}': {e}")
        await asyncio.sleep(1.5)
    return jobs


# ─── LinkedIn ────────────────────────────────────────────────────────────────

async def fetch_linkedin(session: aiohttp.ClientSession) -> list[dict]:
    jobs = []
    queries = [
        "aviation operations manager",
        "project manager aviation Singapore",
        "data analyst airline Singapore",
        "air transport management Singapore",
    ]
    for q in queries:
        try:
            url = (
                f"https://www.linkedin.com/jobs/search"
                f"?keywords={urllib.parse.quote(q)}&location=Singapore"
                f"&sortBy=DD&f_TPR=r86400"  # last 24h
            )
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    cards = soup.select("div.base-card")[:5]
                    for card in cards:
                        title_el = card.select_one("h3.base-search-card__title")
                        company_el = card.select_one("h4.base-search-card__subtitle")
                        location_el = card.select_one("span.job-search-card__location")
                        link_el = card.select_one("a.base-card__full-link")
                        if title_el:
                            jobs.append({
                                "source": "LinkedIn",
                                "title": title_el.get_text(strip=True),
                                "company": company_el.get_text(strip=True) if company_el else "",
                                "location": location_el.get_text(strip=True) if location_el else "Singapore",
                                "url": link_el.get("href", "") if link_el else "",
                                "salary": "",
                                "snippet": "",
                            })
        except Exception as e:
            logger.warning(f"LinkedIn error for '{q}': {e}")
        await asyncio.sleep(1.5)
    return jobs


# ─── Aviation Company Career Portals ─────────────────────────────────────────

AVIATION_PORTALS = [
    {
        "name": "Singapore Airlines",
        "url": "https://careers.singaporeair.com/go/All-Jobs/517600/",
        "company": "Singapore Airlines",
    },
    {
        "name": "Changi Airport Group",
        "url": "https://www.changiairport.com/en/our-story/careers.html",
        "company": "Changi Airport Group",
    },
    {
        "name": "SATS Ltd",
        "url": "https://www.sats.com.sg/careers/job-opportunities",
        "company": "SATS Ltd",
    },
    {
        "name": "ST Engineering",
        "url": "https://careers.stengg.com/en/search/#q=aviation&t=Jobs",
        "company": "ST Engineering",
    },
    {
        "name": "Civil Aviation Authority of Singapore",
        "url": "https://www.caas.gov.sg/who-we-are/careers/current-openings",
        "company": "CAAS",
    },
]

async def fetch_aviation_portals(session: aiohttp.ClientSession) -> list[dict]:
    jobs = []
    for portal in AVIATION_PORTALS:
        try:
            async with session.get(portal["url"], headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    # Generic extraction: look for job-like links
                    links = soup.find_all("a", href=True)
                    found = 0
                    for link in links:
                        text = link.get_text(strip=True)
                        href = link.get("href", "")
                        if len(text) > 10 and _is_relevant_title(text):
                            full_url = href if href.startswith("http") else portal["url"].rstrip("/") + "/" + href.lstrip("/")
                            jobs.append({
                                "source": portal["name"],
                                "title": text[:120],
                                "company": portal["company"],
                                "location": "Singapore",
                                "url": full_url,
                                "salary": "",
                                "snippet": "",
                            })
                            found += 1
                            if found >= 3:
                                break
                    # If nothing matched, add the portal itself as a reference
                    if found == 0:
                        jobs.append({
                            "source": portal["name"],
                            "title": f"Visit {portal['company']} careers page",
                            "company": portal["company"],
                            "location": "Singapore",
                            "url": portal["url"],
                            "salary": "",
                            "snippet": "Check portal for latest openings",
                        })
        except Exception as e:
            logger.warning(f"Portal error for {portal['name']}: {e}")
            jobs.append({
                "source": portal["name"],
                "title": f"Visit {portal['company']} careers page",
                "company": portal["company"],
                "location": "Singapore",
                "url": portal["url"],
                "salary": "",
                "snippet": "Check portal for latest openings",
            })
        await asyncio.sleep(1)
    return jobs


RELEVANT_KEYWORDS = [
    "manager", "analyst", "operations", "aviation", "airport", "airline",
    "project", "data", "planning", "coordinator", "executive", "officer",
    "logistics", "transport", "fleet", "ground", "cargo", "safety", "compliance",
    "strategy", "business", "commercial", "network", "revenue", "finance"
]

def _is_relevant_title(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in RELEVANT_KEYWORDS)


# ─── Deduplication & Relevance Scoring ───────────────────────────────────────

def score_job(job: dict) -> int:
    """Score a job based on relevance to the user's Air Transport Management background."""
    title = (job.get("title") or "").lower()
    score = 0

    high_value = [
        "aviation", "airline", "airport", "air transport", "flight operations",
        "ground handling", "cargo", "atm", "caas", "changi", "iata"
    ]
    medium_value = [
        "project manager", "project management", "data analyst", "data analysis",
        "operations manager", "operations analyst", "business analyst",
        "planning", "strategy", "logistics", "supply chain"
    ]
    bonus = [
        "manager", "director", "head", "lead", "senior", "principal"
    ]

    for kw in high_value:
        if kw in title:
            score += 3
    for kw in medium_value:
        if kw in title:
            score += 2
    for kw in bonus:
        if kw in title:
            score += 1

    return score


def deduplicate(jobs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for job in jobs:
        key = (job["title"].lower()[:40], job["company"].lower()[:30])
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


# ─── Main Entry ──────────────────────────────────────────────────────────────

async def fetch_all_jobs() -> list[dict]:
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            fetch_mcf(session),
            fetch_indeed(session),
            fetch_linkedin(session),
            fetch_aviation_portals(session),
            return_exceptions=True
        )

    all_jobs = []
    for r in results:
        if isinstance(r, list):
            all_jobs.extend(r)
        else:
            logger.warning(f"A source returned an exception: {r}")

    all_jobs = deduplicate(all_jobs)
    all_jobs.sort(key=score_job, reverse=True)
    return all_jobs[:40]  # top 40 most relevant
