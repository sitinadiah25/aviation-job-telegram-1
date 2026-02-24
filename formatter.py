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
    "flight": [
        "Flight Operations Principles", "ICAO/IATA Standards", "Airspace Management",
        "Operational Scheduling", "Aviation Safety & Security"
    ],
    "ground": [
        "Ground Handling Operations", "Turnaround Coordination", "Airport Safety Procedures",
        "Resource Allocation", "Service Level Management"
    ],
    "ramp": [
        "Ramp Operations", "Turnaround Coordination", "Ground Handling",
        "Aviation Safety Procedures", "Aircraft Servicing Protocols"
    ],
    "baggage": [
        "Baggage Handling Systems", "Airport Operations", "Ground Handling",
        "Service Recovery", "Passenger Experience"
    ],
    "air traffic": [
        "Airspace Management", "Air Traffic Flow", "ICAO Procedures",
        "Aviation Safety & Security", "Air Transport Economics"
    ],
    "customer service": [
        "Passenger Experience Management", "Service Excellence", "Complaint Handling",
        "Airport Operations", "Cross-Cultural Communication"
    ],
    "passenger": [
        "Passenger Experience Management", "Airport Terminal Operations",
        "Service Delivery", "Check-in & Boarding Procedures", "Customer Relations"
    ],
    "project": [
        "Project Management", "Stakeholder Management", "Operations Research",
        "Strategic Planning", "Risk Management"
    ],
    "data": [
        "Data Analysis", "Aviation Statistics", "Demand Forecasting",
        "Traffic Flow Analysis", "Operations Research"
    ],
    "business analyst": [
        "Business Analysis", "Process Mapping", "Data Analysis",
        "Stakeholder Management", "Report Writing"
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
    "coordinator": [
        "Coordination & Scheduling", "Stakeholder Communication", "Project Support",
        "Operations Planning", "Documentation & Reporting"
    ],
    "admin": [
        "Administrative Support", "Documentation & Records Management",
        "Scheduling & Coordination", "Office Operations", "Report Writing"
    ],
    "administrative": [
        "Administrative Support", "Documentation & Records Management",
        "Scheduling & Coordination", "Office Operations", "Report Writing"
    ],
    "check-in": [
        "Passenger Experience Management", "Check-in & Boarding Procedures",
        "Airport Customer Service", "IATA Ticketing Standards", "Baggage Handling"
    ],
    "check in": [
        "Passenger Experience Management", "Check-in & Boarding Procedures",
        "Airport Customer Service", "IATA Ticketing Standards", "Baggage Handling"
    ],
    "ticketing": [
        "IATA Ticketing & Fares", "Airline Reservation Systems",
        "Passenger Experience", "Revenue Management Basics", "Customer Service"
    ],
    "counter": [
        "Airport Terminal Operations", "Passenger Experience Management",
        "Check-in & Boarding Procedures", "Customer Relations", "Service Recovery"
    ],
    "guest service": [
        "Passenger Experience Management", "Service Excellence",
        "Airport Terminal Operations", "Complaint Handling", "Cross-Cultural Communication"
    ],
    "business analyst": [
        "Business Analysis", "Process Mapping & Improvement", "Data Analysis",
        "Stakeholder Management", "Aviation Market Research"
    ],
    "junior business": [
        "Business Analysis", "Process Mapping & Improvement", "Data Analysis",
        "Stakeholder Management", "Report Writing"
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


def format_jobs_message(jobs: list[dict], schedule_label: str = None) -> list[str]:
    """Split jobs into Telegram-safe messages (max 4096 chars each)."""
    if not jobs:
        return ["No relevant jobs found at this time. Please check back later."]

    now = datetime.now(SGT).strftime("%d %b %Y, %I:%M %p SGT")
    slot_line = f"🔔 *{schedule_label} SGT Update*\n" if schedule_label else ""
    header = (
        f"✈️ *Aviation & PM Job Listings*\n"
        f"{slot_line}"
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
