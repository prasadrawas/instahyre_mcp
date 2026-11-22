"""
Instahyre MCP Server (Unified 6-Tool Architecture).
A production Model Context Protocol (MCP) server for Instahyre candidate profile management,
matching opportunities, job search, application pipeline, recruiter messages, and privacy settings.
"""
import uuid
import time
from typing import Any, Dict, List, Literal, Optional, Union
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except Exception:
    from mcp.server.fastmcp import FastMCP  # type: ignore
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from instahyre_mcp import auth, client

# Initialize FastMCP server
mcp = FastMCP(
    "instahyre-mcp",
    instructions=(
        "Instahyre MCP Server (Unified 6-Tool Architecture): Production MCP server for Instahyre candidate profile "
        "management, AI-curated matching tech opportunities, job discovery, application pipeline, recruiter interactions, "
        "and employer privacy.\n\n"
        "CORE TOOLS (Total 6 Tools):\n"
        "1. `manage_profile`: Candidate profile reads, section updates (designation, company, skills, salary, notice period), "
        "resume text extraction, resume uploads, and recruiter search pulse.\n"
        "2. `search_jobs`: Discover tech openings. Returns personalized matching feed if query is omitted, or searches 40k+ live jobs.\n"
        "3. `get_job_details`: Comprehensive inspection for single or multiple jobs, extracting structured JD, tech stack, company background, and requirements.\n"
        "4. `manage_job_pipeline`: Complete application lifecycle: express interest/apply, pass/decline, bulk apply, and list applied/declined opportunities.\n"
        "5. `manage_account`: Employer privacy (blocking competitor companies), account settings, recruiter message inbox, and taxonomy autocomplete.\n"
        "6. `manage_session`: Candidate authentication validation and credentials inspection."
    )
)


# ---------------------------------------------------------------------------
# CUSTOM HTTP ROUTES (Health, Landing Page, Multi-Tenant Session Resolver)
# ---------------------------------------------------------------------------

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    """Public health check endpoint for monitoring and cloud container hosting."""
    return JSONResponse({
        "status": "healthy",
        "service": "instahyre-mcp",
        "version": "1.0.0"
    })


@mcp.custom_route("/", methods=["GET", "POST", "OPTIONS", "HEAD"])
async def index_route(request: Request) -> Response:
    """Root info page or transparent redirect to /sse when called with credentials or SSE headers."""
    if request.method == "OPTIONS":
        return Response(status_code=200)

    # Redirect to /sse if query contains auth parameters or accept header requests event-stream
    if (
        "sessionid" in request.query_params
        or "token" in request.query_params
        or "text/event-stream" in request.headers.get("accept", "")
    ):
        from starlette.responses import RedirectResponse
        target_url = "/sse"
        if request.scope.get("query_string"):
            target_url += "?" + request.scope["query_string"].decode("utf-8")
        return RedirectResponse(url=target_url, status_code=307)

    host = request.headers.get("host", "localhost:8000")
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    base_url = f"{scheme}://{host}"
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Instahyre MCP Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 820px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #2d3748; }}
        h1 {{ color: #1a202c; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-top: 10px; }}
        code {{ background: #edf2f7; padding: 3px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; color: #c53030; }}
        pre {{ background: #1a202c; color: #f7fafc; padding: 16px; border-radius: 8px; overflow-x: auto; }}
        pre code {{ background: none; color: inherit; padding: 0; }}
        .badge {{ display: inline-block; background: #38a169; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }}
        .card {{ background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 22px; margin-top: 24px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
        a {{ color: #3182ce; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <span class="badge">Running</span>
    <h1>Instahyre MCP Server</h1>
    <p>Production Model Context Protocol (MCP) server providing automated tools for Instahyre candidate profile management, matching tech opportunities, applications, and recruiter messaging.</p>

    <div class="card">
        <h3>Connect to Claude Web / Claude Desktop / Gemini / Cursor</h3>
        <p>Add this server to your MCP configuration with your personalized SSE URL:</p>
        <pre><code>{{
  "mcpServers": {{
    "instahyre": {{
      "url": "{base_url}/sse?sessionid=YOUR_SESSIONID&csrftoken=YOUR_CSRFTOKEN&cf_clearance=YOUR_CF_CLEARANCE"
    }}
  }}
}}</code></pre>
    </div>

    <div class="card">
        <h3>Unified 6-Tool Architecture</h3>
        <ul>
            <li><code>manage_profile</code>: Complete profile lifecycle, resume text extraction/upload, and activity pulse.</li>
            <li><code>search_jobs</code>: Curated matching feed and full parametric job search across 40,000+ jobs.</li>
            <li><code>get_job_details</code>: Deep inspection for single or multiple jobs with Schema.org JobPosting parsing.</li>
            <li><code>manage_job_pipeline</code>: Apply / interest, pass / decline, bulk apply, and pipeline metrics.</li>
            <li><code>manage_account</code>: Recruiter messaging inbox, employer privacy (blocking companies), and taxonomy autocomplete.</li>
            <li><code>manage_session</code>: Candidate authentication verification and credential inspection.</li>
        </ul>
    </div>
</body>
</html>"""
    return Response(content=html_content, media_type="text/html")


def _bind_multi_tenant_session(request: Request) -> str:
    """Extract and register credentials from URL query parameters or headers."""
    q_sessionid = request.query_params.get("sessionid") or request.query_params.get("token") or ""
    q_csrf = request.query_params.get("csrftoken") or request.query_params.get("csrf") or ""
    q_cf = request.query_params.get("cf_clearance") or request.query_params.get("cf") or ""
    q_ua = request.query_params.get("user_agent") or request.headers.get("user-agent") or ""
    q_resume = request.query_params.get("resume") or ""

    sid = request.query_params.get("sid") or str(uuid.uuid4())
    auth.current_session_id.set(sid)

    if q_sessionid or q_cf or q_csrf:
        auth.SESSION_STORE[sid] = {
            "sessionid": q_sessionid,
            "csrftoken": q_csrf,
            "cf_clearance": q_cf,
            "user_agent": q_ua,
            "resume_url": q_resume,
            "created_at": time.time(),
            "last_seen": time.time()
        }
        auth.current_session_sessionid.set(q_sessionid)
        auth.current_session_csrftoken.set(q_csrf)
        auth.current_session_cf_clearance.set(q_cf)
        auth.current_session_user_agent.set(q_ua)
        auth.current_session_resume_url.set(q_resume)

    auth.clean_stale_sessions()
    return sid


# ---------------------------------------------------------------------------
# CORE TOOLS (Unified 6-Tool Architecture)
# ---------------------------------------------------------------------------

@mcp.tool()
def manage_profile(
    action: Literal["get", "update", "pulse", "get_resume", "upload_resume"] = "get",
    candidate_id: Optional[Union[int, str]] = None,
    personal: Optional[Dict[str, Any]] = None,
    jsp: Optional[Dict[str, Any]] = None,
    resume_file_path: Optional[str] = None,
    extract_text: bool = True,
    max_pages: int = 10,
    sessionid: Optional[str] = None,
    csrftoken: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Candidate profile management: view profile details, update career information/preferences,
    boost recruiter search ranking via activity pulse, and manage resumes.
    Args:
        action: 'get' (view profile and JSP), 'update' (modify provided fields), 'pulse' (bump activity ranking),
                'get_resume' (fetch resume metadata and extracted text), 'upload_resume' (upload local PDF/DOCX)
        candidate_id: Unique candidate ID (optional; automatically inferred if omitted)
        personal: Personal details to update (current_company, current_designation, total_experience, phone, etc.)
        jsp: Job Seeker Profile updates (current_salary, notice_period, location_preferences, status_string, etc.)
        resume_file_path: Absolute local path to resume file for 'upload_resume' action
        extract_text: If True when calling 'get_resume', downloads and parses PDF text via pypdf
        max_pages: Maximum pages to extract when extract_text=True (default: 10)
    """
    if action == "pulse":
        status, res = client.touch_profile_pulse(
            candidate_id=candidate_id,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "result": res}

    elif action == "get_resume":
        status, res = client.download_resume(
            candidate_id=candidate_id,
            extract_text=extract_text,
            max_pages=max_pages,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "result": res}

    elif action == "upload_resume":
        if not resume_file_path:
            return {"status_code": 400, "error": "resume_file_path is required for action='upload_resume'"}
        status, res = client.upload_resume(
            file_path=resume_file_path,
            candidate_id=candidate_id,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "result": res}

    elif action == "update":
        if not personal and not jsp:
            return {"status_code": 400, "error": "At least one of 'personal' or 'jsp' must be provided for action='update'"}
        status, res = client.update_candidate_profile(
            candidate_id=candidate_id,
            personal=personal,
            jsp=jsp,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "result": res}

    else:  # action == "get"
        status, res = client.get_candidate_profile(
            candidate_id=candidate_id,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "profile": res}


@mcp.tool()
def search_jobs(
    query: Optional[str] = None,
    location: Optional[str] = None,
    job_functions: Optional[str] = None,
    limit: int = 30,
    offset: int = 0,
    sessionid: Optional[str] = None,
    csrftoken: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search tech job openings on Instahyre. If query is omitted, automatically returns your
    personalized curated matching feed (opportunities matching your experience and skills).
    Otherwise, executes a parametric search across 40,000+ live jobs.
    Args:
        query: Keywords or role name (e.g. 'Python', 'Full Stack', 'DevOps'). Omit for curated feed.
        location: City or region filter (e.g. 'Bangalore', 'Pune', 'Work From Home')
        job_functions: Job function category ID or string
        limit: Number of results to return (default: 30)
        offset: Offset for pagination (default: 0)
    """
    status, res = client.search_jobs(
        query=query,
        location=location,
        job_functions=job_functions,
        limit=limit,
        offset=offset,
        sessionid=sessionid,
        csrftoken=csrftoken,
        cf_clearance=cf_clearance,
        user_agent=user_agent
    )
    return {"status_code": status, "result": res}


@mcp.tool()
def get_job_details(
    job_ids: Optional[Union[int, str, List[Union[int, str]]]] = None,
    opportunity_url: Optional[str] = None,
    sessionid: Optional[str] = None,
    csrftoken: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inspect job description, company profile, tech stack requirements, and compensation details.
    Supports single or batch job inspection.
    Args:
        job_ids: A single job ID (e.g. 447851) or list of job IDs (e.g. [447851, 470367])
        opportunity_url: Direct opportunity URL path (e.g. '/job-447851-sde-ii-full-stack-at-hoomanely-bangalore/')
    """
    if opportunity_url:
        status, res = client.get_job_details(
            opportunity_url=opportunity_url,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "job": res}

    if not job_ids:
        return {"status_code": 400, "error": "Either job_ids or opportunity_url must be provided"}

    id_list = job_ids if isinstance(job_ids, list) else [job_ids]
    results = []
    overall_status = 200

    for jid in id_list:
        status, res = client.get_job_details(
            job_id=jid,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        if status != 200:
            overall_status = status
        results.append(res)

    if len(results) == 1:
        return {"status_code": overall_status, "job": results[0]}
    return {"status_code": overall_status, "jobs": results, "count": len(results)}


@mcp.tool()
def manage_job_pipeline(
    action: Literal["apply", "pass", "apply_bulk", "list_applied", "list_declined", "metrics"] = "metrics",
    job_id: Optional[Union[int, str]] = None,
    job_ids: Optional[List[Union[int, str]]] = None,
    limit: int = 30,
    offset: int = 0,
    sessionid: Optional[str] = None,
    csrftoken: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manage the candidate application and opportunity pipeline on Instahyre.
    Args:
        action:
            - 'apply': Express interest / apply to a matching opportunity
            - 'pass': Decline / archive an opportunity
            - 'apply_bulk': Apply to multiple opportunities in a single call
            - 'list_applied': Retrieve list of applied / interested opportunities (interest_facet=1)
            - 'list_declined': Retrieve list of passed / declined opportunities (interest_facet=2)
            - 'metrics': Fetch pipeline status counts (total matching, applied, declined)
        job_id: Unique job ID for single 'apply' or 'pass' action
        job_ids: List of job IDs for 'apply_bulk' action
        limit: Max opportunities to return for list actions (default: 30)
        offset: Pagination offset (default: 0)
    """
    if action == "apply":
        if not job_id:
            return {"status_code": 400, "error": "job_id is required for action='apply'"}
        status, res = client.apply_to_opportunity(
            job_id=job_id,
            is_interested=True,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "apply", "job_id": job_id, "result": res}

    elif action == "pass":
        if not job_id:
            return {"status_code": 400, "error": "job_id is required for action='pass'"}
        status, res = client.apply_to_opportunity(
            job_id=job_id,
            is_interested=False,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "pass", "job_id": job_id, "result": res}

    elif action == "apply_bulk":
        if not job_ids:
            return {"status_code": 400, "error": "job_ids list is required for action='apply_bulk'"}
        status, res = client.apply_bulk(
            job_ids=job_ids,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "apply_bulk", "result": res}

    elif action == "list_applied":
        status, res = client.get_matching_opportunities(
            interest_facet=1,
            limit=limit,
            offset=offset,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "list_applied", "result": res}

    elif action == "list_declined":
        status, res = client.get_matching_opportunities(
            interest_facet=2,
            limit=limit,
            offset=offset,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "list_declined", "result": res}

    else:  # action == "metrics"
        status, res = client.get_pipeline_metrics(
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "metrics", "result": res}


@mcp.tool()
def manage_account(
    action: Literal["get_settings", "update_settings", "block_company", "unblock_company", "get_messages", "suggest"] = "get_settings",
    company_name: Optional[str] = None,
    settings_data: Optional[Dict[str, Any]] = None,
    suggest_category: Optional[Literal["locations", "job_functions", "top_employers"]] = "locations",
    candidate_id: Optional[Union[int, str]] = None,
    limit: int = 20,
    offset: int = 0,
    sessionid: Optional[str] = None,
    csrftoken: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Account settings, employer privacy (blocking competitor companies), recruiter message inbox,
    and platform taxonomy autocomplete.
    Args:
        action:
            - 'get_settings': View account settings, privacy, and blocked companies list
            - 'update_settings': Modify account settings or notification preferences
            - 'block_company': Add an employer/competitor to the blocked list
            - 'unblock_company': Remove a company from the blocked list
            - 'get_messages': Inspect recruiter conversations and unread messages in your inbox
            - 'suggest': Fetch platform taxonomy ('locations', 'job_functions', 'top_employers')
        company_name: Name of company to block or unblock
        settings_data: Dictionary of settings to update
        suggest_category: Taxonomy category for 'suggest' ('locations', 'job_functions', 'top_employers')
        candidate_id: Optional candidate ID override
        limit: Number of items to return for inbox/taxonomy
        offset: Offset for pagination
    """
    if action == "block_company":
        if not company_name:
            return {"status_code": 400, "error": "company_name is required for action='block_company'"}
        status, res = client.block_or_unblock_company(
            company_name=company_name,
            action="block",
            candidate_id=candidate_id,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "block_company", "company": company_name, "result": res}

    elif action == "unblock_company":
        if not company_name:
            return {"status_code": 400, "error": "company_name is required for action='unblock_company'"}
        status, res = client.block_or_unblock_company(
            company_name=company_name,
            action="unblock",
            candidate_id=candidate_id,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "unblock_company", "company": company_name, "result": res}

    elif action == "update_settings":
        if not settings_data:
            return {"status_code": 400, "error": "settings_data dictionary is required for action='update_settings'"}
        status, res = client.update_settings(
            candidate_id=candidate_id,
            settings_data=settings_data,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "update_settings", "result": res}

    elif action == "get_messages":
        status, res = client.get_inbox_conversations(
            limit=limit,
            offset=offset,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "get_messages", "result": res}

    elif action == "suggest":
        status, res = client.get_taxonomy(
            taxonomy_type=suggest_category or "locations",
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "suggest", "category": suggest_category, "result": res}

    else:  # action == "get_settings"
        status, res = client.get_settings(
            candidate_id=candidate_id,
            sessionid=sessionid,
            csrftoken=csrftoken,
            cf_clearance=cf_clearance,
            user_agent=user_agent
        )
        return {"status_code": status, "action": "get_settings", "settings": res}


@mcp.tool()
def manage_session(
    action: Literal["validate", "inspect"] = "validate",
    sessionid: Optional[str] = None,
    csrftoken: Optional[str] = None,
    cf_clearance: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Session verification: check active Instahyre session authentication,
    candidate identity, and inspect configured credentials.
    Args:
        action: 'validate' (test live authentication against Instahyre), 'inspect' (show credential presence)
    """
    resolved_sid, resolved_csrf, resolved_cf, resolved_ua = auth.resolve_credentials(
        sessionid=sessionid,
        csrftoken=csrftoken,
        cf_clearance=cf_clearance,
        user_agent=user_agent
    )

    if action == "inspect":
        return {
            "has_sessionid": bool(resolved_sid),
            "sessionid_prefix": resolved_sid[:8] + "..." if resolved_sid else None,
            "has_csrftoken": bool(resolved_csrf),
            "csrftoken_prefix": resolved_csrf[:8] + "..." if resolved_csrf else None,
            "has_cf_clearance": bool(resolved_cf),
            "cf_clearance_prefix": resolved_cf[:12] + "..." if resolved_cf else None,
            "user_agent": resolved_ua
        }

    # action == "validate"
    cid, uid, name = client.get_candidate_identity(
        sessionid=sessionid,
        csrftoken=csrftoken,
        cf_clearance=cf_clearance,
        user_agent=user_agent
    )
    if not cid:
        return {
            "authenticated": False,
            "status_code": 401,
            "error": "Failed to authenticate session with Instahyre. Verify sessionid and cf_clearance tokens."
        }

    return {
        "authenticated": True,
        "status_code": 200,
        "candidate_id": cid,
        "user_id": uid,
        "candidate_name": name,
        "user_agent": resolved_ua
    }


# ---------------------------------------------------------------------------
# DUAL-TRANSPORT MULTI-TENANT ASGI MIDDLEWARE & APP
# ---------------------------------------------------------------------------

class MultiTenantSessionMiddleware:
    """
    ASGI middleware ensuring dynamic multi-tenant session binding.
    Extracts sessionid, csrftoken, cf_clearance, user_agent from URL query parameters
    or headers and propagates them across the asynchronous turn.
    """

    def __init__(self, app_target: Any):
        self.app_target = app_target

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            import urllib.parse
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = urllib.parse.parse_qs(query_string)

            # Extract credentials from URL query parameters
            sid_val = params.get("sessionid", params.get("token", [""]))[0].strip()
            csrf_val = params.get("csrftoken", params.get("csrf", [""]))[0].strip()
            cf_val = params.get("cf_clearance", params.get("cf", [""]))[0].strip()
            ua_val = params.get("user_agent", [""])[0].strip()

            # Extract credentials from HTTP headers if missing
            headers = dict(scope.get("headers", []))
            if not sid_val:
                sid_val = headers.get(b"x-sessionid", headers.get(b"x-instahyre-token", b"")).decode("utf-8").strip()
            if not csrf_val:
                csrf_val = headers.get(b"x-csrftoken", b"").decode("utf-8").strip()
            if not cf_val:
                cf_val = headers.get(b"x-cf-clearance", b"").decode("utf-8").strip()
            if not ua_val:
                ua_val = headers.get(b"user-agent", b"").decode("utf-8").strip()

            if sid_val:
                auth.current_session_sessionid.set(sid_val)
            if csrf_val:
                auth.current_session_csrftoken.set(csrf_val)
            if cf_val:
                auth.current_session_cf_clearance.set(cf_val)
            if ua_val:
                auth.current_session_user_agent.set(ua_val)

            # Intercept response to extract session ID if present
            async def custom_send(message: Any) -> None:
                if message.get("type") == "http.response.start":
                    headers_dict = dict(message.get("headers", []))
                    if b"mcp-session-id" in headers_dict and sid_val:
                        sess_id = headers_dict[b"mcp-session-id"].decode("utf-8").replace("-", "")
                        auth.SESSION_STORE[sess_id] = {
                            "sessionid": sid_val,
                            "csrftoken": csrf_val,
                            "cf_clearance": cf_val,
                            "user_agent": ua_val,
                            "created_at": time.time(),
                            "last_seen": time.time()
                        }
                elif message.get("type") == "http.response.body":
                    body_bytes = message.get("body", b"")
                    if b"session_id=" in body_bytes and sid_val:
                        m = re.search(r"session_id=([a-f0-9\-]+)", body_bytes.decode("utf-8", errors="ignore"))
                        if m:
                            sess_id = m.group(1).replace("-", "")
                            auth.SESSION_STORE[sess_id] = {
                                "sessionid": sid_val,
                                "csrftoken": csrf_val,
                                "cf_clearance": cf_val,
                                "user_agent": ua_val,
                                "created_at": time.time(),
                                "last_seen": time.time()
                            }
                await send(message)

            await self.app_target(scope, receive, custom_send)
            return

        await self.app_target(scope, receive, send)


def get_app() -> Any:
    """Return unified Starlette app supporting both Streamable HTTP (/mcp) and SSE (/sse), with full CORS."""
    from starlette.applications import Starlette
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Route
    from mcp.server.transport_security import TransportSecuritySettings

    sec = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    sse_subapp = mcp.sse_app(transport_security=sec)
    http_subapp = mcp.streamable_http_app(streamable_http_path="/mcp", transport_security=sec)

    http_handler = None
    for r in http_subapp.routes:
        if getattr(r, "path", "") == "/mcp":
            http_handler = r.endpoint
            break

    sse_handler = None
    for r in sse_subapp.routes:
        if getattr(r, "path", "") == "/sse":
            sse_handler = r.endpoint
            break

    routes = [
        Route("/sse", endpoint=sse_handler, methods=["GET", "HEAD"]),
        Route("/sse", endpoint=http_handler, methods=["POST"]),
        Route("/mcp", endpoint=http_handler, methods=["GET", "POST", "HEAD"]),
        Route("/", endpoint=http_handler, methods=["POST"]),
        *[r for r in sse_subapp.routes if getattr(r, "path", "") not in ("/sse", "/mcp")],
    ]

    unified_app = Starlette(
        routes=routes,
        lifespan=http_subapp.router.lifespan_context
    )

    wrapped_session_app = MultiTenantSessionMiddleware(unified_app)
    return CORSMiddleware(
        wrapped_session_app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


app = get_app()


def run_server(transport: str = "stdio", port: Optional[int] = None, host: str = "0.0.0.0") -> None:
    """Run the FastMCP server in either stdio, sse, or streamable-http mode."""
    import os
    if port is None:
        port = int(os.getenv("PORT", 8000))

    if transport == "sse":
        import uvicorn
        import anyio
        print(f"Starting instahyre-mcp in SSE mode on http://{host}:{port} ...")
        app_instance = get_app()
        config = uvicorn.Config(
            app_instance,
            host=host,
            port=port,
            log_level="info",
            timeout_keep_alive=65
        )
        server = uvicorn.Server(config)
        anyio.run(server.serve)
    elif transport == "streamable-http":
        print(f"Starting instahyre-mcp in streamable-http mode on http://{host}:{port} ...")
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")

