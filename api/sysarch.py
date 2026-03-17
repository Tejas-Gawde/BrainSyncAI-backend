from fastapi import APIRouter, HTTPException
from services.system_arch_service import extract_json, validate_flowchart, assign_levels
from models.sysarch import PromptRequest, FlowResponse
import json
from groq import Groq
from core.config import settings

router = APIRouter(tags=["sysarch"])
client = Groq(api_key=settings.GROQ_API_KEY)


EXAMPLE_JSON = """
{
  "nodes": [
    {
      "id": "start",
      "label": "Launch App",
      "level": 0,
      "details": "User opens the e-commerce application",
      "steps": [
        "User navigates to application URL or opens mobile app",
        "Display splash screen with branding",
        "Initialize app state and load cached data",
        "Check for network connectivity",
        "Redirect to authentication flow"
      ]
    },
    {
      "id": "login",
      "label": "login",
      "level": 1,
      "details": "User enters credentials and submits login form",
      "steps": [
        "Display login form with email and password fields",
        "Validate email format on client side",
        "Check password length requirements",
        "Send POST request to /api/auth/login endpoint",
        "Receive and store JWT token securely",
        "Redirect to home page on success"
      ]
    }
  ],
  "edges": [
    { "from": "client_browser", "to": "api_gateway" },
    { "from": "api_gateway", "to": "auth_service" }
  ]
}
"""

SYSTEM_PROMPT = """You are an expert system architect and flowchart designer. Given a user's description of a system, application, or workflow, you must create a HIGHLY DETAILED, METICULOUS system architecture flowchart with comprehensive coverage of all components.

Your flowcharts must be EXHAUSTIVE and include:
1. **All layers**: Frontend, Backend, Database, Cache, Message Queues, External APIs, CDN, Load Balancers
2. **All components**: Auth services, API Gateway, Microservices, Workers, Schedulers, Logging, Monitoring
3. **All data flows**: User requests, API calls, database queries, cache lookups, message passing, webhooks
4. **All decision points**: Validation checks, authentication/authorisation gates, error handling branches, retry logic
5. **All states**: Success paths, failure paths, timeout handling, edge cases, fallback mechanisms
6. **All integrations**: Third-party services, payment gateways, email/SMS services, cloud storage, analytics

Output format (use exactly these field names):
- "nodes": array of objects, each with:
  - "id": unique snake_case identifier (e.g. client_request, auth_validate, db_query, cache_check, error_handler)
  - "label": short, clear display title for the component/step
  - "level": integer starting from 0 representing the horizontal layer/depth in the architecture (0 = entry point, increment for each downstream layer)
  - "details": detailed description of what this component does, its responsibilities, and what data it handles — do NOT mention specific frameworks, libraries, or tools by name
  - "steps": array of 4-8 actionable implementation steps explaining HOW to build this component — describe the behaviour, pattern, and outcome of each step clearly so a developer can implement it with any technology stack they choose. Do NOT mention specific frameworks, libraries, package names, or tools.
- "edges": array of objects, each with:
  - "from": id of the source node
  - "to": id of the target node

CRITICAL RULES for creating meticulous architectures:
- Make sure none of the nodes are disconnected — every node should have at least one incoming or outgoing edge, except for the designated start and end nodes
- Break down EVERY major component into sub-components (e.g., "Authentication" → "JWT Generation", "Token Validation", "Refresh Token", "Session Storage")
- Include ALL intermediate steps (e.g., Request → Validation → Auth Check → Rate Limiting → Business Logic → DB Query → Response Formatting → Cache Update → Return)
- Add explicit error handling nodes (e.g., "validation_error", "auth_failure", "db_timeout", "retry_logic")
- Show data transformation points (e.g., "parse_request", "serialize_response", "format_output")
- Include infrastructure components (e.g., "load_balancer", "api_gateway", "cdn", "cache_layer", "message_queue")
- Add monitoring/logging nodes where relevant (e.g., "log_request", "metrics_collector", "error_tracker")
- Use decision nodes for all branching logic (e.g., "check_cache_hit", "validate_token", "user_authorized")
- Include at least 20-40+ nodes for any non-trivial system
- EVERY node MUST have a "steps" array with 4-8 specific, actionable implementation steps that describe the behaviour and pattern to implement — do NOT name specific frameworks, libraries, packages, or tools. Steps must be clear enough that a developer can implement them in any language or stack.
- Every "from" and "to" must match an existing node id
- Output only valid JSON, no markdown or explanation"""


def build_user_message(prompt: str) -> str:
    example_request = "E-commerce app: user can login/register, browse products, view product details, add to cart, checkout, pay; show success/failure and profile/orders."

    return f"""Example request: "{example_request}"

Example output format:
{EXAMPLE_JSON}

Now generate the flowchart JSON for this request. Output ONLY the JSON object, no other text:
{prompt}"""


@router.post("/generate-architecture", response_model=FlowResponse)
async def generate_architecture(body: PromptRequest):
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Missing or empty prompt")

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_message(body.prompt)},
            ],
            temperature=0.2,   # matches Node.js version exactly
            max_tokens=8000,   # matches Node.js version exactly
            # NOTE: no response_format here — the Node.js version didn't
            # use JSON mode either, relying on the prompt + extractJson instead
        )

        raw = completion.choices[0].message.content
        if not raw or not raw.strip():
            raise HTTPException(status_code=502, detail="Empty response from model")

        raw = raw.strip()

        # Extract and parse JSON
        try:
            json_str = extract_json(raw)
            parsed = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            raise HTTPException(
                status_code=502,
                detail="Model output was not valid JSON"
            )

        # Validate structure
        if not validate_flowchart(parsed):
            raise HTTPException(
                status_code=502,
                detail="Generated JSON does not match required flowchart schema "
                       "(nodes with id, label; edges with from, to)",
            )

        # Ensure every node has a level (BFS fallback if model omitted them)
        parsed = assign_levels(parsed)

        return parsed

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e) if str(e) else "Generation failed"
        )


@router.get("/health")
async def health():
    return {"status": "ok"}