from datetime import datetime
import pytz

SGT = pytz.timezone("Asia/Singapore")

# Skills from an Air Transport Management degree that are useful per job type
ATM_SKILLS_MAP = {
    "aviation": [
        "Air Transport Economics", "Aviation Safety & Security", "Airport Planning & Management",
        "Airline Strategy", "ICAO/IATA Regulations"
    ],
    "airport": [
        "Airport Operations", "Airport Planning & Management", "Passenger Experience",
        "Ground Handling", "Security Compliance"
    ],
    "airline": [
        "Airline Strategy", "Revenue Management", "Network Planning",
        "Airline Economics", "Fleet Planning"
    ],
    "project": [
        "Project Management", "Stakeholder Management", "Operations Research",
        "Strategic Planning", "Risk Management"
    ],
    "data": [
        "Data Analysis", "Aviation Statistics", "Demand Forecasting",
        "Traffic Flow Analysis", "Operations Research"
    ],
    "operations": [
        "Operations Management", "Process Optimisation", "Resource Planning",
        "Service Delivery", "KPI Monitoring"
    ],
    "logistics": [
        "Supply Chain Fundamentals", "Cargo Operations", "Air Freight Management",
        "Transport Economics", "Logistics Planning"
    ],
    "cargo": [
        "Air Cargo Management", "Freight Operations", "Dangerous Goods Regulations",
        "Cargo Revenue Management", "IATA Cargo Standards"
    ],
    "safety": [
        "Aviation Safety Management Systems (SMS)", "Risk Assessment",
        "ICAO Safety Standards", "Safety Auditing", "Incident Investigation"
    ],
    "analyst": [
        "Data Analysis", "Market Research", "Business Intelligence",
        "Statistical Analysis", "Report Writing"
    ],
    "manager": [
        "Leadership & Team Management", "Strategic Planning", "Budget Management",
        "Stakeholder Engagement", "Change Management"
    ],
}

SOURCE_EMOJI = {
    "MyCareersFuture": "🇸🇬",
    "Indeed": "🔍",
    "LinkedIn": "💼",
    "Singapore Airlines": "✈️",
    "Changi Airport Group": "🛬",
    "SATS Ltd": "🛠",
    "ST Engineering": "⚙️",
    "Civil Aviation Authority of Singapore": "🏛",
}


def get_atm_skills(title: str) -> list[str]:
    """Return relevant ATM degree skills for a given job title."""
    title_lower = title.lower()
    skills = set()
    for keyword, skill_list in ATM_SKILLS_MAP.items():
        if keyword in title_lower:
            skills.update(skill_list)
    return list(skills)[:5]  # cap at 5 skills per job


def format_job_entry(job: dict) -> str:
    title = job.get("title", "Untitled")
    company = job.get("company", "")
    location = job.get("location", "")
    url = job.get("url", "")
    salary = job.get("salary", "")
    source = job.get("source", "")
    snippet = job.get("snippet", "")
    emoji = SOURCE_EMOJI.get(source, "📋")

    skills = get_atm_skills(title)

    # Experience level badge
    exp_badge = ""
    if snippet:
        s = snippet.lower()
        if "fresh" in s or ("0" in s and "year" in s):
            exp_badge = "🟢 Fresh Grad Welcome"
        elif "entry" in s:
            exp_badge = "🟢 Entry Level"
        elif "1" in s or "2" in s:
            exp_badge = "🔵 1–2 Years Exp"
        else:
            exp_badge = f"📋 {snippet}"

    lines = []
    lines.append(f"{emoji} *{_escape(title)}*")
    if exp_badge:
        lines.append(exp_badge)
    if company:
        lines.append(f"🏢 {_escape(company)}")
    if location:
        lines.append(f"📍 {_escape(location)}")
    if salary:
        lines.append(f"💰 {_escape(salary)}")
    if skills:
        lines.append(f"🎓 *ATM Skills:* {', '.join(skills)}")
    if url:
        lines.append(f"🔗 [View Job]({url})")

    return "\n".join(lines)


def _escape(text: str) -> str:
    """Escape Markdown special characters."""
    for ch in ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]:
        text = text.replace(ch, f"\\{ch}")
    return text


def format_jobs_message(jobs: list[dict]) -> list[str]:
    """Split jobs into Telegram-safe messages (max 4096 chars each)."""
    if not jobs:
        return ["No relevant jobs found at this time. Please check back later."]

    now = datetime.now(SGT).strftime("%d %b %Y, %I:%M %p SGT")
    header = (
        f"✈️ *Aviation & PM Job Listings*\n"
        f"🎯 Fresh Grad & 1–2 Years Exp\n"
        f"🕐 Updated: {now}\n"
        f"📊 {len(jobs)} jobs found\n"
        f"{'─' * 30}"
    )

    messages = []
    current = header + "\n\n"

    for i, job in enumerate(jobs):
        entry = format_job_entry(job) + "\n\n" + "─" * 30 + "\n\n"
        if len(current) + len(entry) > 4000:
            messages.append(current.strip())
            current = entry
        else:
            current += entry

    if current.strip():
        messages.append(current.strip())

    # Add footer to last message
    messages[-1] += (
        "\n\n💡 *Tip:* Use /latest to refresh at any time\\."
        "\nJobs auto\\-refresh daily at *9:00 AM SGT*\\."
    )

    return messages
