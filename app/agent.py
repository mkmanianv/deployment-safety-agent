import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from app.models import DeploymentRequest, DeploymentVerdict
from app.registry import registry
import app.tools # Ensure tools are imported and registered

load_dotenv()

def get_llm_client() -> tuple[OpenAI, str]:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")  # default is None (OpenAI main endpoint)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model

SYSTEM_PROMPT = """You are a deployment safety advisor.

Your job is to evaluate whether a deployment is safe to proceed.

You must check:
1. Active alerts for the service — any P1/P2 alert is a blocker
2. Change freeze windows for the target region — freeze means NO_GO
3. Recent deployment history — recent failures increase risk

After checking all three, return a JSON verdict with this exact structure:
{
    "verdict": "GO" or "NO_GO",
    "risk_score": 0-100,
    "reasons": ["reason 1", "reason 2"],
    "recommended_actions": ["action 1", "action 2"],
    "safe_to_deploy": true or false
}

Return ONLY the JSON. No other text."""

def evaluate_deployment(request: DeploymentRequest) -> DeploymentVerdict:
    print(f"\nEvaluating deployment: {request.service_name} {request.version} -> {request.target_region}")

    client, model = get_llm_client()
    tools = registry.get_schemas()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Evaluate this deployment request:
Service ID: {request.service_id}
Service Name: {request.service_name}
Version: {request.version}
Target Region: {request.target_region}
Deployed By: {request.deployed_by}

Check all safety conditions and return your verdict."""
        }
    ]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None
        )

        message = response.choices[0].message
        print(f"Agent thinking... finish_reason: {response.choices[0].finish_reason}")

        if response.choices[0].finish_reason == "tool_calls":
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                print(f"  Calling tool: {tool_name}({tool_args})")

                try:
                    tool_result = registry.execute(tool_name, **tool_args)
                    tool_result_str = json.dumps(tool_result)
                except Exception as e:
                    tool_result_str = json.dumps({"error": str(e)})

                print(f"  Tool result: {tool_result_str}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_str
                })

        else:
            verdict_json = message.content.strip()
            # Clean up potential markdown formatting block wrapper returned by some LLMs
            if verdict_json.startswith("```"):
                lines = verdict_json.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                verdict_json = "\n".join(lines).strip()

            try:
                verdict_data = json.loads(verdict_json)
                return DeploymentVerdict(**verdict_data)
            except json.JSONDecodeError:
                raise ValueError(f"Agent returned invalid JSON: {verdict_json}")
