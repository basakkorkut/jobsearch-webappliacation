"""
Job search tools called by the ReAct agent.
Each tool hits the job-service REST API and returns a formatted string result.
"""
import logging
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)

# OpenAI-format tool definitions sent to LM Studio
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": (
                "Search for job postings. Use this when the user asks about available jobs, "
                "positions, or wants to find work opportunities."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Job title or keywords to search for, e.g. 'backend developer', 'data scientist'",
                    },
                    "city": {
                        "type": "string",
                        "description": "City name to filter by, e.g. 'Istanbul', 'Ankara'. Leave empty for all cities.",
                    },
                    "working_preference": {
                        "type": "string",
                        "enum": ["remote", "hybrid", "on_site", ""],
                        "description": "Working preference filter. Leave empty for all types.",
                    },
                    "position_level": {
                        "type": "string",
                        "enum": ["intern", "junior", "mid", "senior", "expert", ""],
                        "description": "Position level filter. Leave empty for all levels.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_job_detail",
            "description": "Get full details of a specific job posting by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The UUID of the job posting.",
                    }
                },
                "required": ["job_id"],
            },
        },
    },
]


async def search_jobs(
    query: str,
    city: str = "",
    working_preference: str = "",
    position_level: str = "",
) -> str:
    params = {"position": query, "limit": 5}
    if city:
        params["city"] = city
    if working_preference:
        params["working_preference"] = working_preference
    if position_level:
        params["position_level"] = position_level

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.job_service_url}/api/v1/search",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("search_jobs tool error: %s", e)
        return "İş arama sırasında bir hata oluştu."

    items = data.get("items", [])
    if not items:
        return f"'{query}' için ilan bulunamadı."

    lines = [f"'{query}' araması için {data.get('total', len(items))} ilan bulundu:\n"]
    for job in items:
        company = job.get("company", {}).get("name", "Bilinmeyen Şirket")
        city_str = job.get("city", "")
        pref = job.get("working_preference", "")
        level = job.get("position_level", "")
        jid = job.get("id", "")
        lines.append(
            f"• [{company}] {job['title']} — {city_str} | {pref} | {level} (id: {jid})"
        )

    return "\n".join(lines)


async def get_job_detail(job_id: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.job_service_url}/api/v1/jobs/{job_id}"
            )
            resp.raise_for_status()
            job = resp.json()
    except Exception as e:
        logger.warning("get_job_detail tool error: %s", e)
        return "İlan detayları alınırken hata oluştu."

    company = job.get("company", {}).get("name", "Bilinmeyen")
    return (
        f"**{job['title']}** — {company}\n"
        f"📍 {job.get('city', '')}, {job.get('country', '')}\n"
        f"💼 {job.get('working_preference', '')} | {job.get('position_level', '')} | {job.get('employment_type', '')}\n"
        f"🏢 {job.get('department', '')}\n\n"
        f"{job.get('description', '')[:500]}..."
    )


# Dispatcher
async def call_tool(name: str, arguments: dict) -> str:
    if name == "search_jobs":
        return await search_jobs(**arguments)
    elif name == "get_job_detail":
        return await get_job_detail(**arguments)
    return f"Bilinmeyen araç: {name}"
