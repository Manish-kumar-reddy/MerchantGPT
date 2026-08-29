"""
The tool-calling conversation loop, using Google's Gemini API (google-genai
SDK) instead of Anthropic. Same manual loop shape as the Anthropic
implementation this replaces: call the model, and if it responds with one or
more `function_call` parts, execute every requested tool, feed the results
back as `function_response` parts, and call the model again -- repeat until
it returns a plain text answer (or a safety cap on iterations is hit).

Automatic function calling (AFC) is explicitly disabled -- the SDK can only
auto-invoke plain Python callables, and our tools need a live AsyncSession +
merchant_id that only this module's caller (app/services/chat.py) has, so
the loop below always drives execution manually via app.agent.tools.execute_tool.

TOOLS (app/agent/tools.py) is left in its existing Anthropic `input_schema`
shape on purpose -- the google-genai SDK's FunctionDeclaration accepts a raw
JSON Schema dict directly via `parameters_json_schema`, so no separate schema
dialect or converter is needed here. This keeps the tool definitions and
their SQL/analytics execution (app/agent/tools.py, app/services/analytics.py)
completely provider-agnostic; only this file is Gemini-specific.

This module is exercised by a live integration path only when GEMINI_API_KEY
is set -- it cannot be meaningfully unit tested offline since its entire job
is calling a real external API. Every tool it can call, and the SQL those
tools run, *is* unit/integration tested elsewhere (see tests/test_revenue_leaks.py,
test_segmentation.py, test_churn.py, and the live route checks in the
verification pass).
"""

import json
from uuid import UUID

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import TOOLS, execute_tool
from app.core.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are MerchantGPT, an AI growth manager embedded in an e-commerce merchant's dashboard.

You have read-only tools to query the merchant's real sales, customer, cart, and refund data. Rules:
- Never guess or estimate a number you could look up with a tool. Call the relevant tool first.
- When you cite a number, state where it came from (e.g. "based on the last 30 days of orders").
- Be direct and specific. Merchants want actions, not hedged generalities.
- If a finding has a dollar impact, lead with it.
- You cannot send emails, issue refunds, or change prices. You can only analyze and recommend -- say so if asked to take an action directly.
"""

MAX_TOOL_ITERATIONS = 5

_FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name=tool["name"],
        description=tool["description"],
        parameters_json_schema=tool["input_schema"],
    )
    for tool in TOOLS
]
_GEMINI_TOOLS = [types.Tool(function_declarations=_FUNCTION_DECLARATIONS)]


class AgentNotConfiguredError(Exception):
    """Raised when GEMINI_API_KEY is not set. Callers should catch this and
    degrade gracefully rather than 500."""


def _get_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise AgentNotConfiguredError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=settings.gemini_api_key)


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


def _to_gemini_contents(conversation: list[dict]) -> list[types.Content]:
    return [
        types.Content(role=_to_gemini_role(turn["role"]), parts=[types.Part(text=turn["content"])])
        for turn in conversation
    ]


async def run_agent_turn(
    *,
    db: AsyncSession,
    merchant_id: UUID,
    conversation: list[dict],
    extra_context: str | None = None,
) -> tuple[str, list[str]]:
    """
    `conversation` is a list of {"role": "user"|"assistant", "content": ...}
    dicts (already including the new user turn) -- provider-agnostic on the
    way in; converted to Gemini's Content/Part format here. `extra_context`,
    if given, is appended to the system prompt -- used to inject
    semantically-retrieved past chat turns (see app/services/chat.py).
    Returns (final_text_reply, tool_names_called).
    """
    client = _get_client()
    contents = _to_gemini_contents(conversation)
    tools_called: list[str] = []
    system_instruction = SYSTEM_PROMPT if not extra_context else f"{SYSTEM_PROMPT}\n\n{extra_context}"

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=_GEMINI_TOOLS,
        max_output_tokens=settings.gemini_max_output_tokens,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        parts = candidate.content.parts or []
        function_calls = [p.function_call for p in parts if p.function_call is not None]

        if not function_calls:
            text_parts = [p.text for p in parts if p.text]
            return "\n".join(text_parts).strip(), tools_called

        contents.append(candidate.content)

        function_response_parts = []
        for call in function_calls:
            tools_called.append(call.name)
            try:
                result = await execute_tool(call.name, dict(call.args or {}), db, merchant_id)
            except Exception as exc:
                # Intentionally broad: a tool failure should surface to the model as a tool
                # error it can react to, not crash the whole chat turn.
                result = {"error": str(exc)}

            # Gemini's function_response must be a plain JSON-primitive dict (no Decimal/UUID/date
            # objects) -- round-trip through json.dumps(default=str) the same way the previous
            # Anthropic implementation did before sending tool_result text.
            safe_result = json.loads(json.dumps(result, default=str))
            function_response_parts.append(types.Part.from_function_response(name=call.name, response={"result": safe_result}))

        contents.append(types.Content(role="user", parts=function_response_parts))

    return (
        "I gathered a lot of data but couldn't finish reasoning about it in time -- try asking a more specific "
        "question.",
        tools_called,
    )
