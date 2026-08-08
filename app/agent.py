import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from app.models import DeploymentRequest, DeploymentVerdict
from app.tools import check_active_alerts, check_change_freeze, get_recent_deployments

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_active_alerts",
            "description": "Check if there are active alerts for a service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The service ID to check alerts for"
                    }
                },
                "required": ["service_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_change_freeze",
            "description": "Check if a change freeze is active for a region",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "The region to check freeze window for"
                    }
                },
                "required": ["region"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_deployments",
            "description": "Get recent deployment history for a service",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The service ID to get deployment history for"
                    }
                },
                "required": ["service_id"]
            }
        }
    }
]

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

def run_tool(tool_name: str, tool_args: dict) -> str:
    if tool_name == "check_active_alerts":
        result = check_active_alerts(**tool_args)
    elif tool_name == "check_change_freeze":
        result = check_change_freeze(**tool_args)
    elif tool_name == "get_recent_deployments":
        result = get_recent_deployments(**tool_args)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result)

def evaluate_deployment(request: DeploymentRequest) -> DeploymentVerdict:
    print(f"\nEvaluating deployment: {request.service_name} {request.version} -> {request.target_region}")

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
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        print(f"Agent thinking... finish_reason: {response.choices[0].finish_reason}")

        if response.choices[0].finish_reason == "tool_calls":
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                print(f"  Calling tool: {tool_name}({tool_args})")

                tool_result = run_tool(tool_name, tool_args)
                print(f"  Tool result: {tool_result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        else:
            verdict_json = message.content.strip()
            verdict_data = json.loads(verdict_json)
            return DeploymentVerdict(**verdict_data)
