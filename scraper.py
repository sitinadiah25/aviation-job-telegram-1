import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import urllib.parse

logger = logging.getLogger(__name__)

# Keywords relevant to the user's background (entry-level focused)
SEARCH_QUERIES = [
    "aviation executive",
    "airport operations executive",
    "airline operations executive",
    "junior data analyst aviation",
    "air transport associate",
    "flight operations officer",
    "ground handling officer",
    "project coordinator aviation",
    "operations analyst entry level",
    "graduate aviation",
]

# Titles that suggest too much seniority — used to filter out irrelevant roles
SENIOR_TITLE_KEYWORDS = [
    "senior", "sr.", "lead", "head of", "director", "vp ", "vice president",
    "chief", "principal", "general manager", "gm ", "c-suite", "coo", "ceo",
    "cto", "cfo", "svp", "evp", "partner", "managing director"
]

# Entry-level positive signals in titles
ENTRY_LEVEL_TITLE_SIGNALS = [
    "junior", "associate", "graduate", "trainee", "intern", "entry",
    "assistant", "officer", "executive", "analyst", "coordinator", "specialist"
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
        "aviation", "air transport", "data analyst", "airport", "airline",
        "project coordinator", "operations executive", "graduate trainee"
    ]
    for keyword in keywords[:6]:  # limit requests
        try:
            # MCF supports filtering by max years of experience via the API
            url = (
                f"https://www.mycareersfuture.gov.sg/api/v2/search"
                f"?search={urllib.parse.quote(keyword)}&limit=15&page=0"
                f"&sortBy=new_posting_date"
                f"&minimumYearsExperience=0&maximumYearsExperience=2"
            )
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    for item in results:
                        min_exp = item.get("minimumYearsExperience", 0) or 0
                        max_exp = item.get("maximumYearsExperience", 2) or 2
                        # Only include jobs asking for 0–2 years experience
                        if min_exp <= 2:
                            title = item.get("title", "")
                            if not _is_senior_title(title):
                                jobs.append({
                                    "source": "MyCareersFuture",
                                    "title": title,
                                    "company": item.get("postedCompany", {}).get("name", ""),
                                    "location": "Singapore",
                                    "url": f"https://www.mycareersfuture.gov.sg/job/{item.get('uuid', '')}",
                                    "salary": _mcf_salary(item),
                                    "snippet": _mcf_exp_label(min_exp, max_exp),
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


def _mcf_exp_label(min_exp: int, max_exp: int) -> str:
    if min_exp == 0 and max_exp <= 1:
        return "Fresh graduate welcome"
    if min_exp == 0:
        return f"0–{max_exp} years experience"
    return f"{min_exp}–{max_exp} years experience"


def _is_senior_title(title: str) -> bool:
    """Return True if the title signals a senior/leadership role to filter out."""
    t = title.lower()
    return any(kw in t for kw in SENIOR_TITLE_KEYWORDS)


# ─── Indeed (Singapore) ──────────────────────────────────────────────────────

async def fetch_indeed(session: aiohttp.ClientSession) -> list[dict]:
    jobs = []
    queries = [
        ("aviation executive entry level", "Singapore"),
        ("junior data analyst aviation", "Singapore"),
        ("airport operations officer", "Singapore"),
        ("graduate trainee aviation", "Singapore"),
        ("project coordinator aviation fresh graduate", "Singapore"),
    ]
    for q, loc in queries:
        try:
            # &explvl=entry_level filters Indeed to entry-level postings
            url = (
                f"https://sg.indeed.com/jobs"
                f"?q={urllib.parse.quote(q)}&l={urllib.parse.quote(loc)}"
                f"&sort=date&explvl=entry_level"
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
                            title = title_el.get_text(strip=True)
                            if _is_senior_title(title):
                                continue
                            job_id = link_el.get("data-jk", "")
                            jobs.append({
                                "source": "Indeed",
                                "title": title,
                                "company": company_el.get_text(strip=True) if company_el else "",
                                "location": location_el.get_text(strip=True) if location_el else "Singapore",
                                "url": f"https://sg.indeed.com/viewjob?jk={job_id}" if job_id else f"https://sg.indeed.com{link_el.get('href','')}",
                                "salary": "",
                                "snippet": "Entry level",
                            })
        except Exception as e:
            logger.warning(f"Indeed error for '{q}': {e}")
        await asyncio.sleep(1.5)
    return jobs


# ─── LinkedIn ────────────────────────────────────────────────────────────────

async def fetch_linkedin(session: aiohttp.ClientSession) -> list[dict]:
    jobs = []
    queries = [
        "aviation operations executive Singapore",
        "junior data analyst aviation Singapore",
        "airport operations officer Singapore",
        "air transport associate Singapore",
        "project coordinator aviation Singapore",
    ]
    for q in queries:
        try:
            # f_E=2 = Entry level on LinkedIn
            url = (
                f"https://www.linkedin.com/jobs/search"
                f"?keywords={urllib.parse.quote(q)}&location=Singapore"
                f"&sortBy=DD&f_TPR=r86400&f_E=2"  # last 24h + entry level
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
                            title = title_el.get_text(strip=True)
                            if _is_senior_title(title):
                                continue
                            jobs.append({
                                "source": "LinkedIn",
                                "title": title,
                                "company": company_el.get_text(strip=True) if company_el else "",
                                "location": location_el.get_text(strip=True) if location_el else "Singapore",
                                "url": link_el.get("href", "") if link_el else "",
                                "salary": "",
                                "snippet": "Entry level",
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
    snippet = (job.get("snippet") or "").lower()
    score = 0

    high_value = [
        "aviation", "airline", "airport", "air transport", "flight operations",
        "ground handling", "cargo", "atm", "caas", "changi", "iata"
    ]
    medium_value = [
        "project coordinator", "data analyst", "data analysis",
        "operations analyst", "business analyst", "operations executive",
        "planning", "logistics", "supply chain"
    ]
    entry_level_bonus = [
        "junior", "associate", "graduate", "trainee", "officer",
        "executive", "coordinator", "assistant", "entry"
    ]

    for kw in high_value:
        if kw in title:
            score += 3
    for kw in medium_value:
        if kw in title:
            score += 2
    for kw in entry_level_bonus:
        if kw in title:
            score += 2

    # Boost if explicitly flagged as fresh-grad friendly
    if "fresh" in snippet or "graduate" in snippet or "entry" in snippet:
        score += 3

    # Penalise any senior role that slipped through
    if _is_senior_title(title):
        score -= 10

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
